try:
    from qt.core import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
                         QComboBox, QTableWidget, QTableWidgetItem, QPushButton,
                         QHeaderView, QLineEdit, QFileDialog, QGroupBox)
except ImportError:
    from PyQt5.Qt import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
                          QComboBox, QTableWidget, QTableWidgetItem, QPushButton,
                          QHeaderView, QLineEdit, QFileDialog, QGroupBox)

from .config import prefs

# Qt6 moved QHeaderView.Stretch to QHeaderView.ResizeMode.Stretch
_STRETCH = getattr(QHeaderView, 'Stretch',
                   getattr(getattr(QHeaderView, 'ResizeMode', None), 'Stretch', 1))


class ConfigWidget(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        self.l = QVBoxLayout()
        self.setLayout(self.l)
        self.setMinimumWidth(750)
        self.setMinimumHeight(900)

        self.l.addWidget(QLabel('<b>Replacement Options:</b>'))
        # ---------------------------------------------------------------
        # Individual profanity word families
        # ---------------------------------------------------------------
        profanity_group = QGroupBox('Profanity — individual word families')
        profanity_layout = QVBoxLayout()

        self.damn = QCheckBox('Replace d*** variants')
        self.damn.setChecked(prefs.get('replace_damn', True))
        profanity_layout.addWidget(self.damn)

        self.bitch = QCheckBox('Replace b**** variants')
        self.bitch.setChecked(prefs.get('replace_bitch', True))
        profanity_layout.addWidget(self.bitch)

        self.shit = QCheckBox('Replace s*** variants')
        self.shit.setChecked(prefs.get('replace_shit', True))
        profanity_layout.addWidget(self.shit)

        self.fbomb = QCheckBox('Replace f*** variants')
        self.fbomb.setChecked(prefs.get('replace_fbomb', True))
        profanity_layout.addWidget(self.fbomb)

        self.hell = QCheckBox('Replace h*** variants')
        self.hell.setChecked(prefs.get('replace_hell', True))
        profanity_layout.addWidget(self.hell)

        profanity_group.setLayout(profanity_layout)
        self.l.addWidget(profanity_group)

        # ---------------------------------------------------------------
        # "Ass" interpretation group
        # ---------------------------------------------------------------
        ass_group = QGroupBox('Donkey language')
        ass_layout = QVBoxLayout()
        ass_note = QLabel(
            '<small>The word "*ss" has two very different meanings. '
            'Choose whether to assume usage is an insult or to assume '
            'it refers to a donkey.\n'
            'Compound words (sm*rt-*ss, j*ck*ss, k*ss-*ss, etc.) are always '
            'replaced regardless of this setting.</small>'
        )
        ass_note.setWordWrap(True)
        ass_layout.addWidget(ass_note)

        self.replace_ass = QCheckBox('Replace *ss / *rse (standalone and compound words)')
        self.replace_ass.setChecked(prefs.get('replace_ass', True))
        ass_layout.addWidget(self.replace_ass)

        h_ass = QHBoxLayout()
        h_ass.addWidget(QLabel('Standalone "*ss" / "*rse" means:'))
        self.ass_mode = QComboBox()
        self.ass_mode.addItems([
            'auto-detect',
            'insult',
            'donkey',
        ])
        # Map stored value → combo index
        _ass_stored = prefs.get('ass_mode', 'auto')
        _ass_idx = {'auto': 0, 'dirty': 1, 'clean': 2}.get(_ass_stored, 0)
        self.ass_mode.setCurrentIndex(_ass_idx)
        h_ass.addWidget(self.ass_mode)
        ass_layout.addLayout(h_ass)

        ass_group.setLayout(ass_layout)
        self.l.addWidget(ass_group)

        # ---------------------------------------------------------------
        # Religious language group
        # ---------------------------------------------------------------
        religious_group = QGroupBox('Religious language')
        religious_layout = QVBoxLayout()

        self.religious = QCheckBox(
            'Replace uses of God / Jesus / Christ\n'
            '(e.g. "Thank God", "My God!", "For God\'s sake")'
        )
        self.religious.setChecked(prefs.get('replace_religious', True))
        religious_layout.addWidget(self.religious)

        vain_note = QLabel(
            '<small><b>Exclamatory / vain uses</b> — Exclamatory means '
            'use of God\'s name as an outburst rather than a prayer. '
            'Reverential means usage is not in vain.</small>'
        )
        vain_note.setWordWrap(True)
        religious_layout.addWidget(vain_note)

        h_vain = QHBoxLayout()
        h_vain.addWidget(QLabel('Exclamatory "Lord" usage:'))
        self.vain_lord = QComboBox()
        self.vain_lord.addItems([
            'auto-detect',
            'always exclamatory',
            'always reverential',
        ])
        # Map stored value → combo index
        _vain_stored = prefs.get('replace_vain_lord', 'auto')
        _vain_idx = {'auto': 0, 'always': 1, 'never': 2}.get(_vain_stored, 0)
        self.vain_lord.setCurrentIndex(_vain_idx)
        h_vain.addWidget(self.vain_lord)
        religious_layout.addLayout(h_vain)

        self.replace_god = QCheckBox(
            'Replace ALL occurrences of "God" and "Christ"\n'
            'Warning: broad — catches narration, theology, character names, etc.'
        )
        self.replace_god.setChecked(prefs.get('replace_god', False))
        religious_layout.addWidget(self.replace_god)

        religious_group.setLayout(religious_layout)
        self.l.addWidget(religious_group)

        # ---------------------------------------------------------------
        # Crude language group
        # ---------------------------------------------------------------
        crude_group = QGroupBox('Crude language')
        crude_layout = QVBoxLayout()
        crude_note = QLabel(
            '<small>Body-part references, bathroom humour, and crude compound words '
            '(cr*p, d*ck, b*stard, etc.)</small>'
        )
        crude_note.setWordWrap(True)
        crude_layout.addWidget(crude_note)
        self.crude = QCheckBox('Replace crude language')
        self.crude.setChecked(prefs.get('replace_crude', True))
        crude_layout.addWidget(self.crude)
        crude_group.setLayout(crude_layout)
        self.l.addWidget(crude_group)

        # ---------------------------------------------------------------
        # Slurs group
        # ---------------------------------------------------------------
        slur_group = QGroupBox('Slurs')
        slur_layout = QVBoxLayout()
        self.slurs = QCheckBox('Replace racial / ethnic slurs')
        self.slurs.setChecked(prefs.get('replace_slurs', True))
        slur_layout.addWidget(self.slurs)
        slur_group.setLayout(slur_layout)
        self.l.addWidget(slur_group)

        # ---------------------------------------------------------------
        # Custom replacements table
        # ---------------------------------------------------------------
        self.l.addWidget(QLabel('<b>Custom Replacements:</b>'))
        hint = QLabel(
            '<small>Find supports Python regular expressions '
            '(e.g. <tt>\\\\bword\\\\b</tt>). '
            'Replace may use backreferences (e.g. <tt>\\\\1</tt>). '
            'Uncheck <i>Regex</i> to match the text literally.</small>'
        )
        hint.setWordWrap(True)
        self.l.addWidget(hint)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Find', 'Replace', 'Ignore Case', 'Regex'])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(_STRETCH)
        self.l.addWidget(self.table)

        hb = QHBoxLayout()
        self.add_row_button = QPushButton('Add Row')
        self.add_row_button.clicked.connect(lambda: self._add_table_row([]))
        hb.addWidget(self.add_row_button)
        self.remove_row_button = QPushButton('Remove Row')
        self.remove_row_button.clicked.connect(self._remove_table_row)
        hb.addWidget(self.remove_row_button)
        self.l.addLayout(hb)

        # ---------------------------------------------------------------
        # Live tester
        # ---------------------------------------------------------------
        self.l.addWidget(QLabel('<b>Test Replacements:</b>'))
        htest = QHBoxLayout()
        self.test_input = QLineEdit()
        self.test_input.setPlaceholderText('Enter sample text to test rules…')
        self.test_input.returnPressed.connect(self._test_replacements)
        htest.addWidget(self.test_input)
        test_btn = QPushButton('Test')
        test_btn.clicked.connect(self._test_replacements)
        htest.addWidget(test_btn)
        self.l.addLayout(htest)

        self.test_output = QLineEdit()
        self.test_output.setPlaceholderText('Resulting text will appear here…')
        self.test_output.setReadOnly(True)
        self.l.addWidget(self.test_output)

        for data in prefs.get('custom_replacements', []):
            self._add_table_row(data)

        # ---------------------------------------------------------------
        # Backup / confirmation / logging
        # ---------------------------------------------------------------
        misc_group = QGroupBox('General options')
        misc_layout = QVBoxLayout()

        self.backup = QCheckBox('Create backup of original file (ORIGINAL_FORMAT)')
        self.backup.setChecked(prefs.get('create_backup', True))
        misc_layout.addWidget(self.backup)

        self.confirm = QCheckBox('Show confirmation dialog before cleaning')
        self.confirm.setChecked(prefs.get('show_confirm_dialog', True))
        misc_layout.addWidget(self.confirm)

        self.show_setup = QCheckBox('Mute plugin setup instructions')
        self.show_setup.setChecked(prefs.get('mute_setup_warning', False))
        misc_layout.addWidget(self.show_setup)

        hlog = QHBoxLayout()
        self.write_log = QCheckBox('Write change logs to directory:')
        self.write_log.setChecked(prefs.get('write_log', False))
        hlog.addWidget(self.write_log)
        self.log_dir = QLineEdit()
        _default_log = ""
        self.log_dir.setPlaceholderText('%s' % _default_log)
        self.log_dir.setText(prefs.get('log_dir', ''))
        hlog.addWidget(self.log_dir)
        browse_btn = QPushButton('Browse…')
        browse_btn.clicked.connect(self._browse_log_dir)
        hlog.addWidget(browse_btn)
        misc_layout.addLayout(hlog)

        misc_group.setLayout(misc_layout)
        self.l.addWidget(misc_group)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _vain_stored_value(self):
        """Return the internal stored value for the vain_lord combo."""
        return {0: 'auto', 1: 'always', 2: 'never'}.get(
            self.vain_lord.currentIndex(), 'auto')

    def _ass_stored_value(self):
        """Return the internal stored value for the ass_mode combo."""
        return {0: 'auto', 1: 'dirty', 2: 'clean'}.get(
            self.ass_mode.currentIndex(), 'auto')

    def _browse_log_dir(self):
        current = self.log_dir.text().strip() or ''
        chosen = QFileDialog.getExistingDirectory(self, 'Select log directory', current)
        if chosen:
            self.log_dir.setText(chosen)

    def _make_checkbox_cell(self, checked):
        """Return a centred checkbox widget for a table cell."""
        cb = QCheckBox()
        cb.setChecked(checked)
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.addWidget(cb)
        layout.setContentsMargins(0, 0, 0, 0)
        container.setLayout(layout)
        container.checkbox = cb
        return container

    def _add_table_row(self, data):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(data[0] if data else ''))
        self.table.setItem(row, 1, QTableWidgetItem(data[1] if len(data) > 1 else ''))
        # col 2: ignore case (default True)
        self.table.setCellWidget(row, 2, self._make_checkbox_cell(
            data[2] if len(data) > 2 else True))
        # col 3: is_regex (default False)
        self.table.setCellWidget(row, 3, self._make_checkbox_cell(
            data[3] if len(data) > 3 else False))

    def _remove_table_row(self):
        self.table.removeRow(self.table.currentRow())

    def _cell_checkbox(self, row, col):
        container = self.table.cellWidget(row, col)
        return container.checkbox if container else None

    def _get_custom_rules(self):
        """Parse the table into a list of (pattern, replace, pcase_fn) tuples."""
        import re
        from .cleaner import keep_case
        rules = []
        for row in range(self.table.rowCount()):
            item_find = self.table.item(row, 0)
            find = item_find.text().strip() if item_find else ''
            item_replace = self.table.item(row, 1)
            replace = item_replace.text() if item_replace else ''
            if not find:
                continue

            cb_case = self._cell_checkbox(row, 2)
            cb_regex = self._cell_checkbox(row, 3)
            ignore_case = cb_case.isChecked() if cb_case else True
            is_regex = cb_regex.isChecked() if cb_regex else False

            flags = re.I if ignore_case else 0
            try:
                pattern = find if is_regex else re.escape(find)
                pat = re.compile(pattern, flags)
                pcase_fn = False if is_regex else keep_case
                rules.append((pat, replace, pcase_fn))
                # Clear any previous error highlighting
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(self.palette().base())
            except Exception as e:
                # Highlight invalid regex rows in red
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        try:
                            from qt.core import QColor
                        except ImportError:
                            from PyQt5.Qt import QColor
                        item.setBackground(QColor(255, 200, 200))
                raise ValueError('Invalid regex in row %d: %s' % (row + 1, e))
        return rules

    def _test_replacements(self):
        from .cleaner import language_check, RuleEngine
        try:
            custom_rules = self._get_custom_rules()
        except ValueError as e:
            from calibre.gui2 import error_dialog
            return error_dialog(self, 'Regex Error', str(e), show=True)

        sample = self.test_input.text()
        if not sample:
            self.test_output.setText('')
            return

        rules = language_check(
            sample,
            vain_override=self._vain_stored_value(),
            ass_override=self._ass_stored_value(),
            replace_slurs=self.slurs.isChecked(),
            replace_crude=self.crude.isChecked(),
            replace_damn=self.damn.isChecked(),
            replace_bitch=self.bitch.isChecked(),
            replace_shit=self.shit.isChecked(),
            replace_fbomb=self.fbomb.isChecked(),
            replace_hell=self.hell.isChecked(),
            replace_religious=self.religious.isChecked(),
            replace_ass=self.replace_ass.isChecked(),
            replace_god=self.replace_god.isChecked(),
        )
        rules.extend(custom_rules)
        engine = RuleEngine(rules)
        cleaned = engine.process_line(sample)
        self.test_output.setText(cleaned)

    def commit(self):
        try:
            # Validate custom rules first
            self._get_custom_rules()

            custom = []
            for row in range(self.table.rowCount()):
                item_find = self.table.item(row, 0)
                find = item_find.text().strip() if item_find else ''
                if not find:
                    continue
                item_replace = self.table.item(row, 1)
                replace = item_replace.text() if item_replace else ''
                cb_case = self._cell_checkbox(row, 2)
                cb_regex = self._cell_checkbox(row, 3)
                ignore_case = cb_case.isChecked() if cb_case else True
                is_regex = cb_regex.isChecked() if cb_regex else False
                custom.append([find, replace, ignore_case, is_regex])

            prefs.set('replace_slurs',    self.slurs.isChecked())
            prefs.set('replace_crude',    self.crude.isChecked())
            prefs.set('replace_damn',     self.damn.isChecked())
            prefs.set('replace_bitch',    self.bitch.isChecked())
            prefs.set('replace_shit',     self.shit.isChecked())
            prefs.set('replace_fbomb',    self.fbomb.isChecked())
            prefs.set('replace_hell',     self.hell.isChecked())
            prefs.set('replace_religious', self.religious.isChecked())
            prefs.set('replace_god',       self.replace_god.isChecked())
            prefs.set('replace_vain_lord', self._vain_stored_value())
            prefs.set('replace_ass',       self.replace_ass.isChecked())
            prefs.set('ass_mode',          self._ass_stored_value())
            prefs.set('create_backup',     self.backup.isChecked())
            prefs.set('show_confirm_dialog', self.confirm.isChecked())
            prefs.set('mute_setup_warning', self.show_setup.isChecked())
            prefs.set('write_log',         self.write_log.isChecked())
            prefs.set('log_dir',           self.log_dir.text().strip())
            prefs.set('custom_replacements', custom)

        except ValueError as e:
            from calibre.gui2 import error_dialog
            error_dialog(self, 'Configuration Error',
                         'One or more custom replacements are invalid.',
                         det_msg=str(e), show=True)
            return False
        except Exception as e:
            from calibre.gui2 import error_dialog
            error_dialog(self, 'Configuration Error',
                         'An unexpected error occurred while saving.',
                         det_msg=str(e), show=True)
            return False
        return True
