from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import (
    Dispatcher, error_dialog, info_dialog, question_dialog, gprefs
)
from calibre.gui2.threaded_jobs import ThreadedJob
import html
import os
import re
import tempfile

from calibre.utils.config import config_dir
try:
    from qt.core import QTimer, QIcon, QPixmap, QMenu, QDialog, \
        QVBoxLayout, QLabel, QDialogButtonBox, QPushButton, \
        QTextEdit, Qt
except ImportError:
    from PyQt5.Qt import QTimer, QIcon, QPixmap, QMenu, QDialog, \
        QVBoxLayout, QLabel, QDialogButtonBox, QPushButton, \
        QTextEdit, Qt

try:
    from calibre.gui2.dialogs.choose_format import ChooseFormatDialog
except ImportError:
    ChooseFormatDialog = None

# Format preference order used by both clean and preview.
_FORMAT_PREFERENCE = ['epub', 'azw3', 'mobi', 'htmlz', 'zip', 'html', 'txt']


def _pick_format(formats):
    """Return the best format string (lower-case) from a list of available formats."""
    if not formats:
        return None
    fmt = next((p for p in _FORMAT_PREFERENCE
                if p.upper() in formats or p in formats), None)
    return fmt if fmt is not None else list(formats)[0].lower()


# ---------------------------------------------------------------------------
# Worker functions — run in a background thread by ThreadedJob.
#
# THREADING RULES:
#   • Workers must NOT call any db write methods (add_format, etc.).
#     Those emit Qt change signals and will crash if called off the GUI thread.
#   • All file export (db.copy_format_to) happens on the GUI thread before the
#     job starts, so workers only do pure file I/O — no db calls at all.
#   • All Qt object creation/manipulation happens only in callbacks (GUI thread).
# ---------------------------------------------------------------------------

def _worker_clean(work_items, prefs_snapshot, abort, log, notifications):
    """
    Process pre-exported ebook files.

    work_items:     list of dicts { 'book_id', 'title', 'fmt', 'path' }
    prefs_snapshot: plain dict of prefs values read on the GUI thread —
                    must never be a JSONConfig/QSettings object.

    Returns the same list with 'changes_made', 'count', and 'error' added.
    """
    total = len(work_items)

    from . import clean_ebook_file

    for idx, item in enumerate(work_items):
        if abort.is_set():
            log.warn('Aborted by user after %d/%d books.' % (idx, total))
            for remaining in work_items[idx:]:
                if 'changes_made' not in remaining:
                    remaining.update(changes_made=False, count=0, error='Aborted')
            break

        notifications.put((idx / total, 'Book %d of %d' % (idx + 1, total)))

        title = item['title']
        fmt   = item['fmt']
        path  = item['path']

        log.info('[%d/%d] Cleaning "%s" (%s) ...' % (idx + 1, total, title, fmt.upper()))

        try:
            # Collect diffs silently (log=None suppresses "Cleaning ..." noise)
            # before the file is modified in-place.
            _dr_ok, diffs = clean_ebook_file(
                path, log=None, dry_run=True, prefs_snapshot=prefs_snapshot, title=title)

            # clean_ebook_file modifies the file at 'path' in-place.
            changes_made, count = clean_ebook_file(
                path, log=log, prefs_snapshot=prefs_snapshot, title=title)

            if changes_made:
                log.info('  -> %d replacement(s) made.' % count)
                if diffs:
                    current_file = None
                    for fname, orig, repl in diffs:
                        if fname != current_file:
                            current_file = fname
                            log.info('    [%s]' % fname)
                        log.info('      - %s' % orig)
                        log.info('      + %s' % repl)
            else:
                log.info('  -> No changes needed.')

            item.update(changes_made=changes_made, count=count, error=None)
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            log.error('[ERROR] "%s": %s\n%s' % (title, e, tb))
            item.update(changes_made=False, count=0, error=str(e))

    log.info('\nProcessing complete.')
    return work_items


def _worker_preview(item, prefs_snapshot, abort, log, notifications):
    """
    Dry-run a single pre-exported ebook file.

    item:           dict { 'book_id', 'title', 'fmt', 'path' }
    prefs_snapshot: plain dict of prefs values read on the GUI thread.

    Returns: { 'title', 'changes', 'error' }
    """
    title = item['title']
    path  = item['path']
    fmt   = item['fmt']

    log.info('Previewing "%s" (%s) ...' % (title, fmt.upper()))
    notifications.put((0.1, 'Scanning for changes ...'))

    from . import clean_ebook_file

    try:
        _changes_made, changes = clean_ebook_file(
            path, log=log, dry_run=True, prefs_snapshot=prefs_snapshot, title=title)
        notifications.put((1.0, 'Done'))

        if changes:
            log.info('%d change(s) found across %d file(s).'
                     % (len(changes), len(set(f for f, _, __ in changes))))
            for fname, orig, clean in changes:
                log.info('  [%s]  %r  ->  %r' % (fname, orig, clean))
        else:
            log.info('No changes would be made.')

        return dict(title=title, changes=changes, error=None)

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        log.error('Preview failed: %s\n%s' % (e, tb))
        return dict(title=title, changes=[], error=str(e))


# ---------------------------------------------------------------------------
# InterfaceAction
# ---------------------------------------------------------------------------

class CleanerAction(InterfaceAction):

    name = 'Language Cleaner'
    action_spec = ('Clean', 'images/clean.png',
                   'Replace offensive language in selected books', 'Alt+Shift+C')
    action_type = 'current'
    action_add_menu = True

    def genesis(self):
        """Called once when Calibre sets up the toolbar button."""
        icon_data = self.load_resources(['images/clean.png'])
        if icon_data.get('images/clean.png'):
            pm = QPixmap()
            pm.loadFromData(icon_data['images/clean.png'])
            self.qaction.setIcon(QIcon(pm))

        self.qaction.triggered.connect(self.clean_selected_books)

        menu = self.qaction.menu()
        if menu is None:
            menu = QMenu()
            self.qaction.setMenu(menu)

        self.create_menu_action(
            menu,
            'clean_language',
            'Clean Selected Books',
            triggered=self.clean_selected_books,
        )
        self.create_menu_action(
            menu,
            'preview_language_clean',
            'Preview Language Changes',
            triggered=self.preview_selected_books,
        )
        self.create_menu_action(
            menu,
            'configure_language_clean',
            'Configure…',
            triggered=self.show_configuration,
        )

    def show_configuration(self):
        """Open the plugin configuration dialog."""
        self.interface_action_base_plugin.do_user_config(parent=self.gui)

    def _action_in_bar(self, bar):
        """Return True if our qaction is present in the given toolbar/menubar."""
        try:
            return self.qaction in bar.actions()
        except Exception:
            return False

    def is_in_context_menu(self):
        """Check if this plugin's action is in the library right-click context menu."""
        try:
            return self._action_in_bar(self.gui.library_view.context_menu)
        except Exception:
            pass
        # Fallback: gprefs key (may not exist on all versions)
        layout = gprefs.get('action-layout-context-menu', [])
        return any(
            (item[0] if isinstance(item, (list, tuple)) else item) == self.name
            for item in layout
        )

    def is_on_any_toolbar(self):
        """Check if this plugin's action is in any toolbar or menubar."""
        try:
            for bar in self.gui.bars_manager.bars:
                if self._action_in_bar(bar):
                    return True
            # Also check the menu bar
            if self._action_in_bar(self.gui.bars_manager.menu_bar):
                return True
        except Exception:
            pass
        # Fallback: gprefs keys (may not exist on all versions)
        for key in ('action-layout-toolbar', 'action-layout-main', 'action-layout-menubar'):
            layout = gprefs.get(key, [])
            if any(
                (item[0] if isinstance(item, (list, tuple)) else item) == self.name
                for item in layout
            ):
                return True
        return False

    def _missing_locations_desc(self, missing_toolbar, missing_context):
        """Return a short human-readable description of what is missing."""
        if missing_toolbar and missing_context:
            return 'a <b>toolbar button</b> or the <b>right-click context menu</b>'
        if missing_toolbar:
            return 'a <b>toolbar button</b>'
        return 'the <b>right-click context menu</b>'

    def show_setup_instructions(self, missing_toolbar, missing_context):
        """
        Step 2 — non-modal how-to dialog so the user can click Preferences behind it.
        Uses QDialog + d.show() instead of exec_() so it does not block the GUI.
        """

        missing_desc = self._missing_locations_desc(missing_toolbar, missing_context)

        steps_html = ''
        if missing_toolbar:
            steps_html += (
                '<li>For the <b>toolbar</b>: choose '
                '<i>"The main toolbar"</i> from the dropdown</li>'
            )
        if missing_context:
            steps_html += (
                '<li>For the <b>right-click menu</b>: choose '
                '<i>"The context menu for the books in the calibre library"</i> '
                'from the dropdown</li>'
            )

        body = (
            '<p><b>Language Cleaner</b> is not yet visible in %s.</p>'
            '<p>This dialog stays open — follow the steps, then close it when done:</p>'
            '<ol>'
            '<li>Open <b>Preferences &rarr; Toolbars &amp; Menus</b></li>'
            '%s'
            '<li>Find <b>Clean</b> (Language Cleaner) in the left-hand list</li>'
            '<li>Click the <b>&rarr;</b> arrow to add it to the right-hand list</li>'
            '<li>Click <b>Apply</b></li>'
            '<li>Repeat for other locations, then restart Calibre</li>'
            '</ol>'
            '<p><i>Tip: switch the dropdown and click Apply again to add it to '
            'multiple locations without closing Preferences.</i></p>'
        ) % (missing_desc, steps_html)

        d = QDialog(self.gui)
        d.setWindowTitle('How to add Language Cleaner')
        d.setWindowFlags(d.windowFlags() | Qt.WindowStaysOnTopHint)
        d.resize(520, 360)
        layout = QVBoxLayout(d)
        label = QLabel(body)
        label.setWordWrap(True)
        label.setOpenExternalLinks(False)
        layout.addWidget(label)
        btn_box = QDialogButtonBox()
        close_btn = btn_box.addButton('Close', QDialogButtonBox.AcceptRole)
        close_btn.clicked.connect(d.accept)
        layout.addWidget(btn_box)
        # show() is non-modal — returns immediately, dialog stays open
        d.show()
        # Keep a reference so the dialog isn't garbage-collected
        self._setup_instructions_dialog = d

    def show_setup_notice(self, missing_toolbar, missing_context):
        """
        Step 1 — 3-button compact prompt:
          "Show me how"   → open non-modal instructions, remind again next launch
          "Remind me later" → dismiss, remind again next launch (no prefs change)
          "Don't remind me" → silence permanently
        Uses a custom QDialog because calibre's question_dialog only supports 2 buttons.
        """

        missing_desc = self._missing_locations_desc(missing_toolbar, missing_context)

        body = (
            '<p><b>Language Cleaner</b> is installed but has not been added to '
            '%s yet.</p>'
            '<p>Would you like instructions on how to add it?</p>'
        ) % missing_desc

        d = QDialog(self.gui)
        d.setWindowTitle('Language Cleaner — Setup')
        d.resize(420, 160)
        layout = QVBoxLayout(d)
        label = QLabel(body)
        label.setWordWrap(True)
        layout.addWidget(label)

        btn_box = QDialogButtonBox()
        show_btn   = btn_box.addButton('Show me how',     QDialogButtonBox.AcceptRole)
        later_btn  = btn_box.addButton('Remind me later', QDialogButtonBox.RejectRole)
        never_btn  = btn_box.addButton("Don't remind me", QDialogButtonBox.DestructiveRole)

        result = {'choice': 'later'}  # default if window is just closed

        def _on_show():
            result['choice'] = 'show'
            d.accept()

        def _on_later():
            result['choice'] = 'later'
            d.reject()

        def _on_never():
            result['choice'] = 'never'
            d.accept()

        show_btn.clicked.connect(_on_show)
        later_btn.clicked.connect(_on_later)
        never_btn.clicked.connect(_on_never)
        layout.addWidget(btn_box)
        d.exec_()

        if result['choice'] == 'show':
            self.show_setup_instructions(missing_toolbar, missing_context)
        elif result['choice'] == 'never':
            from .config import prefs
            prefs.set('mute_setup_warning', True)
        # 'later' and window-close both do nothing — shows again next launch


    def initialization_complete(self):
        """Called once when the Calibre GUI is fully initialized."""
        from .config import prefs

        # Reset mute flag on reinstall or upgrade by comparing the mtime of
        # the installed plugin zip.  Calibre writes this file on every install,
        # so its mtime changes even for same-version reinstalls, while normal
        # Calibre restarts leave it untouched.
        # Do this immediately (before the timer) so the flag is correct when
        # the deferred check runs.
        try:
            zip_path = os.path.join(config_dir, 'plugins', 'Language Cleaner.zip')
            fingerprint = str(os.path.getmtime(zip_path))
            stored_fp = prefs.get('plugin_fingerprint', None)
            if stored_fp != fingerprint:
                prefs.set('plugin_fingerprint', fingerprint)
                prefs.set('mute_setup_warning', False)
        except Exception:
            pass

        if prefs.get('mute_setup_warning', False):
            return

        # Defer the layout check until after Calibre finishes its own
        # post_initialize_actions.  Running it synchronously here causes
        # an AttributeError ('Main' has no attribute 'listener') because
        # parts of the main window aren't ready yet.  A zero-delay singleShot
        # queues our callback at the back of the current event loop iteration,
        # by which time Calibre's initialization is complete.
        QTimer.singleShot(0, self._deferred_setup_check)

    def _deferred_setup_check(self):
        """Runs after the event loop is idle — Calibre is fully initialized."""
        missing_toolbar = not self.is_on_any_toolbar()
        missing_context = not self.is_in_context_menu()

        if missing_toolbar or missing_context:
            self.show_setup_notice(missing_toolbar, missing_context)

    def library_view_context_menu_actions(self, event, menu):
        """Called when Calibre's library context menu is about to be shown."""
        return [self.qaction]


    def location_selected(self, loc):
        self.qaction.setEnabled(loc == 'library')

    # ------------------------------------------------------------------
    # GUI-thread helpers
    # ------------------------------------------------------------------

    def _choose_format(self, formats, title):
        """
        Show Calibre's standard format-chooser dialog.
        Returns the chosen format string (lower-case) or None if cancelled.
        Falls back to auto-pick if the dialog is unavailable.
        """
        if ChooseFormatDialog is None or not formats:
            return _pick_format(formats) if formats else None
        d = ChooseFormatDialog(self.gui, title, list(formats))
        if d.exec_():
            return d.format().lower()
        return None  # user cancelled

    def _export_book(self, db, book_id, forced_fmt=None):
        """
        Export a book's format to a plain OS temp file.
        forced_fmt: already-chosen format (lower-case); if None, auto-pick.
        Returns (fmt_str, path) or (None, None) if no formats exist.
        Called on the GUI thread only — never inside a worker.
        """
        formats = db.formats(book_id)
        if not formats:
            return None, None
        fmt = forced_fmt if forced_fmt else _pick_format(formats)
        fd, path = tempfile.mkstemp(suffix='.' + fmt)
        os.close(fd)
        db.copy_format_to(book_id, fmt.upper(), path)
        return fmt, path

    @staticmethod
    def _remove_tempfiles(items):
        """Delete temp files from a list of work-item dicts."""
        for item in items:
            for key in ('path', 'original_path'):
                p = item.get(key)
                if p and os.path.exists(p):
                    try:
                        os.remove(p)
                    except OSError:
                        pass

    @staticmethod
    def _snapshot_prefs():
        """
        Read all prefs values into a plain dict on the GUI thread.

        calibre's JSONConfig is backed by QSettings, which is a QObject and
        must only be accessed on the thread it was created on (the GUI thread).
        Workers receive this plain dict instead of the live prefs object so
        they never touch QSettings off-thread.
        """
        from .config import prefs
        return {k: prefs.get(k, v) for k, v in prefs.defaults.items()}

    # ------------------------------------------------------------------
    # Clean
    # ------------------------------------------------------------------

    def clean_selected_books(self):
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows:
            return error_dialog(self.gui, 'No books selected',
                                'Select one or more books to clean.', show=True)

        book_ids = self.gui.library_view.get_selected_ids()
        db = self.gui.current_db.new_api

        # ------------------------------------------------------------------
        # Format selection
        # For a single book with multiple formats: show the standard Calibre
        # format-chooser so the user can pick exactly which format to clean.
        # For multiple books: auto-pick the best format per book (prompting
        # per book would be unworkable), but surface the choices in the
        # confirmation dialog so the user can see what will be touched.
        # ------------------------------------------------------------------
        forced_formats = {}   # book_id -> chosen fmt (lower-case)

        if len(book_ids) == 1:
            book_id = book_ids[0]
            formats = db.formats(book_id)
            if formats and len(formats) > 1:
                title = db.field_for('title', book_id) or ('ID %d' % book_id)
                chosen = self._choose_format(
                    formats,
                    'Choose format to clean for "%s"' % title,
                )
                if chosen is None:
                    return   # user cancelled the format dialog
                forced_formats[book_id] = chosen

        prefs_snapshot = self._snapshot_prefs()
        if prefs_snapshot.get('show_confirm_dialog', True):
            # Build a per-book summary line for the confirmation message
            lines = []
            for book_id in book_ids:
                title = db.field_for('title', book_id) or ('ID %d' % book_id)
                if book_id in forced_formats:
                    fmt_hint = ' [%s]' % forced_formats[book_id].upper()
                else:
                    avail = db.formats(book_id) or []
                    auto = _pick_format(avail)
                    # Show the format hint if we auto-picked one from multiple,
                    # or if it's ZIP (to be clear).
                    if auto and (len(avail) > 1 or auto.lower() == 'zip'):
                        fmt_hint = ' [%s]' % auto.upper()
                    else:
                        fmt_hint = ''
                lines.append('  - %s%s' % (title, fmt_hint))

            detail = '\n'.join(lines) if len(book_ids) <= 20 else ''
            msg = ('Clean language in %d book(s)? This will modify the stored '
                   'files in your library.' % len(book_ids))
            if detail:
                msg += '\n\n' + detail

            if not question_dialog(
                self.gui, 'Clean Language', msg
            ):
                return

        # Export every book to a temp file HERE on the GUI thread.
        # The worker then only does pure file I/O — no db calls at all.
        work_items = []
        export_errors = []
        for book_id in book_ids:
            title = db.field_for('title', book_id) or ('ID %d' % book_id)
            try:
                fmt, path = self._export_book(
                    db, book_id, forced_fmt=forced_formats.get(book_id))
                if fmt is None:
                    export_errors.append('"%s" — no formats available.' % title)
                else:
                    work_items.append(dict(book_id=book_id, title=title,
                                           fmt=fmt, path=path))
            except Exception as e:
                export_errors.append('"%s" — export failed: %s' % (title, e))

        if not work_items:
            msg = 'No books could be exported for cleaning.'
            if export_errors:
                msg += '\n\n' + '\n'.join(export_errors)
            return error_dialog(self.gui, 'Nothing to clean', msg, show=True)

        desc = 'Language Cleaner: cleaning %d book(s)' % len(work_items)
        job = ThreadedJob(
            'language_cleaner_clean',
            desc,
            func=_worker_clean,
            args=(work_items, self._snapshot_prefs()),
            kwargs={},
            callback=Dispatcher(self._on_clean_complete),
        )
        self.gui.job_manager.run_threaded_job(job)
        self.gui.status_bar.show_message(
            'Language Cleaner: %d book(s) queued...' % len(work_items), 3000)

    def _on_clean_complete(self, job):
        """
        Callback — runs on the GUI thread after the clean worker finishes.
        db.add_format is called here (GUI thread) so Qt change signals are
        always emitted from the correct thread.
        """
        results = job.result or []

        if job.failed:
            self._remove_tempfiles(results)
            error_dialog(self.gui, 'Language Cleaner Error',
                         'The cleaning job failed.',
                         det_msg=job.details or str(getattr(job, 'result', '')),
                         show=True)
            return

        from .config import prefs
        do_backup = prefs.get('create_backup', True)
        db = self.gui.current_db.new_api
        cleaned = 0
        skipped = 0
        errors  = []
        updated = []

        for item in results:
            path = item.get('path')
            book_id = item['book_id']
            fmt = item['fmt'].upper()

            if item.get('error'):
                errors.append((book_id, item['title'], item['error']))
            elif item.get('changes_made'):
                try:
                    # Handle Backup the standard Calibre way
                    if do_backup:
                        # save_original_format copies the CURRENT library file to 
                        # ORIGINAL_FMT if it doesn't already exist.
                        db.save_original_format(book_id, fmt)

                    # Update Main Format
                    db.add_format(book_id, fmt, path, replace=True)
                    
                    cleaned += 1
                    updated.append(book_id)
                except Exception as e:
                    import traceback
                    print(traceback.format_exc())
                    errors.append((book_id, item['title'], str(e)))
            else:
                skipped += 1

            # Cleanup temporary file
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

        if updated:
            # 1. Update the main library list (columns)
            self.gui.library_view.model().refresh_ids(updated)

            # 2. Increment the refresh cookie if present (helps with some UI caching)
            if hasattr(self.gui, 'refresh_cookie'):
                self.gui.refresh_cookie += 1

            # 3. Refresh the tag browser counts
            self.gui.tags_view.recount()

            # 4. Force the Book Details panel to show the updated format list.
            #
            # save_original_format() adds ORIGINAL_EPUB (etc.) to the db but
            # does not emit the signal that Book Details listens to, so the
            # panel keeps its stale cached format list until the user clicks
            # away and back.
            #
            # Emitting current_changed(idx, idx) tells the library-view model
            # the current row changed, causing it to re-query the db and push
            # the full updated book data (including new formats) to the Book
            # Details panel — the same thing that happens when the user clicks
            # away and back.
            #
            # Note: gui.book_details is a QSplitter in Calibre 9+ and has no
            # refresh(book_id) method, so we do NOT call it directly.
            current_idx = self.gui.library_view.currentIndex()
            if current_idx.isValid():
                self.gui.library_view.model().current_changed(
                    current_idx, current_idx)

        summary_lines = [
            'Cleaned:          %d book(s)' % cleaned,
            'No change needed: %d book(s)' % skipped,
        ]

        if errors:
            summary_lines.append('Errors:           %d book(s)' % len(errors))

        summary = '\n'.join(summary_lines)

        if errors:
            detail_lines = []
            for book_id, title, err_msg in errors:
                detail_lines.append('"%s" (ID %d):' % (title, book_id))
                detail_lines.append('  ' + err_msg)
                # Surface actionable advice for the common KF8/MOBI limitation
                if 'KF8' in err_msg:
                    detail_lines.append(
                        '  Tip: This MOBI file uses the old format that cannot be cleaned directly.\n'
                        '  To fix:\n'
                        '    1. Right-click the book -> Convert books -> Convert individually\n'
                        '    2. Set Output format to MOBI\n'
                        '    3. Open the "MOBI output" section\n'
                        '    4. Set "MOBI file type" to "new" (KF8)\n'
                        '    5. Click OK, then clean the newly converted file.'
                    )
                detail_lines.append('')
            error_dialog(
                self.gui, 'Language Cleaner Complete',
                summary,
                det_msg='\n'.join(detail_lines).strip(),
                show=True,
            )
        else:
            info_dialog(self.gui, 'Language Cleaner Complete',
                        summary, show=True)

    # ------------------------------------------------------------------
    # Preview
    # ------------------------------------------------------------------

    def preview_selected_books(self):
        book_ids = self.gui.library_view.get_selected_ids()
        if not book_ids:
            return error_dialog(self.gui, 'No books selected',
                                'Select one or more books to preview.', show=True)

        book_id = book_ids[0]
        db = self.gui.current_db.new_api
        title = db.field_for('title', book_id) or ('ID %d' % book_id)

        # If the book has multiple formats, let the user choose which to preview.
        formats = db.formats(book_id)
        if not formats:
            return error_dialog(self.gui, 'No formats',
                                '"%s" has no formats to preview.' % title, show=True)

        forced_fmt = None
        if len(formats) > 1:
            forced_fmt = self._choose_format(
                formats,
                'Choose format to preview for "%s"' % title,
            )
            if forced_fmt is None:
                return   # user cancelled

        try:
            fmt, path = self._export_book(db, book_id, forced_fmt=forced_fmt)
        except Exception as e:
            return error_dialog(self.gui, 'Export Error',
                                'Could not export "%s": %s' % (title, e), show=True)

        if fmt is None:
            return error_dialog(self.gui, 'No formats',
                                '"%s" has no formats to preview.' % title, show=True)

        item = dict(book_id=book_id, title=title, fmt=fmt, path=path)
        desc = 'Language Cleaner: previewing "%s"' % title
        job = ThreadedJob(
            'language_cleaner_preview',
            desc,
            func=_worker_preview,
            args=(item, self._snapshot_prefs()),
            kwargs={},
            callback=Dispatcher(self._on_preview_complete),
        )
        self.gui.job_manager.run_threaded_job(job)
        self.gui.status_bar.show_message('Language Cleaner preview started...', 3000)

    def _on_preview_complete(self, job):
        """Callback — runs on the GUI thread after the preview worker finishes."""
        try:
            path = job.args[0]['path']   # item dict is still args[0]
            if path and os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

        if job.failed:
            error_dialog(self.gui, 'Language Cleaner Preview Error',
                         'The preview job failed unexpectedly.',
                         det_msg=job.details, show=True)
            return

        result = job.result
        if result is None:
            return

        err = result.get('error')
        if err:
            detail_lines = [err]
            if 'KF8' in err:
                detail_lines.append(
                    '\nTip: This MOBI file uses the old format that cannot be cleaned directly.\n'
                    'To fix:\n'
                    '  1. Right-click the book -> Convert books -> Convert individually\n'
                    '  2. Set Output format to MOBI\n'
                    '  3. Open the "MOBI output" section\n'
                    '  4. Set "MOBI file type" to "new" (KF8)\n'
                    '  5. Click OK, then preview the newly converted file.'
                )
            error_dialog(
                self.gui, 'Preview Error',
                'An error occurred while generating the preview.',
                det_msg='\n'.join(detail_lines).strip(),
                show=True
            )
            return

        changes = result.get('changes', [])
        title   = result.get('title', '')
        if not changes:
            info_dialog(self.gui, 'Preview',
                        'No changes would be made to "%s".' % title, show=True)
        else:
            self._show_diff_dialog(changes)

    # ------------------------------------------------------------------
    # Diff dialog (GUI thread only)
    # ------------------------------------------------------------------

    def _show_diff_dialog(self, changes):

        d = QDialog(self.gui)
        d.setWindowTitle('Language Cleaner - Preview Changes')
        d.resize(900, 600)
        layout = QVBoxLayout(d)
        layout.addWidget(QLabel('%d change(s) in %d file(s).' % (
            len(changes), len(set(f for f, _, __ in changes)))))

        text = QTextEdit()
        text.setReadOnly(True)

        rows = []
        current_file = None
        for fname, orig, clean in changes:
            if fname != current_file:
                current_file = fname
                rows.append(
                    '<tr><td colspan="2" style="background:#e0e0e0; color:#000000; '
                    'padding:3px 6px; font-size:11px;">%s</td></tr>'
                    % html.escape(fname)
                )
            rows.append(
                '<tr>'
                '<td style="background:#ffdddd; color:#000000; padding:5px 8px; '
                'width:50%%; vertical-align:top;">%s</td>'
                '<td style="background:#ddffdd; color:#000000; padding:5px 8px; '
                'width:50%%; vertical-align:top;">%s</td>'
                '</tr>'
                % (self._mark_changed_words(orig, clean),
                   self._mark_changed_words(clean, orig))
            )

        text.setHtml(
            '<html><body style="color:#000000;">'
            '<table style="width:100%%; border-collapse:collapse; font-size:13px;">'
            + ''.join(rows) + '</table></body></html>'
        )
        layout.addWidget(text)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(d.reject)
        layout.addWidget(buttons)
        d.exec_()

    def _mark_changed_words(self, text, other):
        """Bold words in text that do not appear in other."""
        other_words = set(w.lower() for w in re.split(r'\W+', other) if w)
        out = []
        for part in re.split(r'(\W+)', text):
            escaped = html.escape(part)
            if re.search(r'\w', part) and part.lower() not in other_words:
                out.append('<b style="color:#990000;">%s</b>' % escaped)
            else:
                out.append(escaped)
        return ''.join(out)
