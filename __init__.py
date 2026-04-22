#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
import time
import os
import mimetypes
import re
import tempfile
import zipfile

# Relative imports for plugin modules are generally more robust in Calibre's
# zip-importer environment.  We import language_check and keep_case here,
# but RuleEngine is imported inside the functions that use it to avoid
# potential partially-initialized module errors during complex reloads.
from .cleaner import language_check, keep_case

# TemporaryDirectory and walk are intentionally NOT imported from calibre.ebooks.tweak:
#   - calibre's TemporaryDirectory spawns a QProcess (safe_atexit) which must be
#     created on the GUI thread — using it in a worker thread causes Qt crashes.
#   - We use stdlib tempfile.TemporaryDirectory and os.walk instead (Qt-free).
from calibre.ebooks.tweak import get_tools, WorkerError, Error
from calibre.customize import InterfaceActionBase

__license__ = 'GPL v3'
__copyright__ = '2012, Jordan Anderson'
__docformat__ = 'restructuredtext en'

# ---------------------------------------------------------------------------
# Maps from legacy config-widget display strings to internal cleaner.py values.
# The new config_widget stores 'auto'/'always'/'never' and 'auto'/'dirty'/'clean'
# directly, but these maps keep backward-compat for any saved prefs that still
# hold the old display strings.
# ---------------------------------------------------------------------------
_VAIN_MAP = {
    'assume vulgar': 'always', 'assume respectful': 'never', 'auto': 'auto',
    # new combo labels (stored as internal values now, but keep for safety)
    'always': 'always', 'never': 'never',
    'always exclamatory — replace (Tom Clancy style)': 'always',
    'always reverential — keep as-is (C.S. Lewis style)': 'never',
    'auto-detect': 'auto',
}
_ASS_MAP = {
    'assume insult': 'dirty', 'assume donkey': 'clean', 'auto': 'auto',
    'dirty': 'dirty', 'clean': 'clean',
    'rear end / insult — replace (Tom Clancy style)': 'dirty',
    'donkey — keep as-is (C.S. Lewis style)': 'clean',
    'auto-detect': 'auto',
}


def _walk(root):
    """Yield all file paths under root (stdlib os.walk, Qt-free)."""
    for dirpath, _dirnames, filenames in os.walk(root):
        for filename in filenames:
            yield os.path.join(dirpath, filename)


try:
    from calibre.utils.logging import prints
except ImportError:
    prints = print

try:
    try:
        from bs4 import BeautifulSoup, NavigableString
    except ImportError:
        from calibre.ebooks.BeautifulSoup import BeautifulSoup, NavigableString
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


# ---------------------------------------------------------------------------
# HTML / text cleaning helpers
# ---------------------------------------------------------------------------

def clean_html_content(html_text, engine):
    """Apply replacements to visible text nodes only; return (cleaned_html, count)."""
    if not BS4_AVAILABLE:
        # Improved fallback: only replace text between > and <, or at start/end.
        # Still naive, but handles document boundaries better.
        def _sub_visible(m):
            # Very basic check to avoid processing content of script/style tags
            # by looking at the tag immediately preceding the match.
            # This is not perfect but better than nothing for a regex-only fallback.
            prefix = m.group(1)
            if '<script' in prefix.lower() or '<style' in prefix.lower():
                return m.group(0)
            return m.group(1) + engine.process_line(m.group(2)) + m.group(3)

        # Match text between tags, or between start/end and tags.
        # We include the preceding tag to check for script/style.
        pattern = re.compile(r'(^|>[^<]*)([^<>]+)(<|$)')
        cleaned = pattern.sub(_sub_visible, html_text)
        return cleaned, 1 if cleaned != html_text else 0

    soup = BeautifulSoup(html_text, 'html.parser')
    SKIP_TAGS = {'script', 'style', 'code', 'pre', 'head', 'title'}
    replacement_count = 0
    for element in soup.find_all(string=True):
        if element.parent.name in SKIP_TAGS:
            continue
        original = str(element)
        cleaned = engine.process_line(original)
        if cleaned != original:
            replacement_count += 1
            element.replace_with(NavigableString(cleaned))
    return str(soup), replacement_count


def _clean_text_content(text, engine):
    """Apply replacements line-by-line; return (cleaned_text, count)."""
    output_lines = []
    replacement_count = 0
    for line in text.split('\n'):
        cleaned = engine.process_line(line)
        if cleaned != line:
            replacement_count += 1
        output_lines.append(cleaned)
    return '\n'.join(output_lines), replacement_count


# ---------------------------------------------------------------------------
# File utilities
# ---------------------------------------------------------------------------

def _decode_bytes(raw):
    """Try common encodings in order; return (decoded_text, encoding) or (None, None)."""
    if raw.startswith(b'\xef\xbb\xbf'):
        return raw.decode('utf-8-sig'), 'utf-8-sig'
    if raw.startswith(b'\xff\xfe'):
        return raw.decode('utf-16-le'), 'utf-16-le'
    if raw.startswith(b'\xfe\xff'):
        return raw.decode('utf-16-be'), 'utf-16-be'

    for enc in ('utf-8', 'windows-1252', 'windows-1250'):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            pass
    return None, None


def read_file_with_encoding(path):
    """Try common encodings in order; raise UnicodeDecodeError if all fail."""
    with open(path, 'rb') as f:
        raw = f.read()
    text, enc = _decode_bytes(raw)
    if text is None:
        raise UnicodeDecodeError('utf-8', b'', 0, 1, 'All encodings failed for %s' % path)
    return text, enc


def _get_ftype(f):
    """Return MIME type for f, with fallback for common HTML extensions."""
    ftype = mimetypes.guess_type(f)[0]
    if not ftype and f.lower().endswith(('.html', '.xhtml')):
        return 'text/html'
    return ftype


def _get_logdir(prefs_snapshot=None):
    """
    Return the directory to write change logs to, or None if logging is off.
    Respects the write_log and log_dir prefs; creates the default dir if needed.
    """
    _p = prefs_snapshot if prefs_snapshot is not None else _load_prefs_direct()
    if not _p.get('write_log', False):
        return None

    custom_dir = _p.get('log_dir', '')
    if custom_dir:
        if os.path.isdir(custom_dir):
            return custom_dir
        # User requested failure if path doesn't exist
        raise RuntimeError('Log directory does not exist: %s' % custom_dir)

    from calibre.utils.config import config_dir
    default = os.path.join(config_dir, 'language_cleaner_logs')
    os.makedirs(default, exist_ok=True)
    return default


def _load_prefs_direct():
    """Load prefs from JSONConfig — only called when no snapshot is available."""
    try:
        from .config import prefs
        # If it doesn't have a standard defaults dict, it might be a mock.
        # Return the object itself so that mock side_effects/return_values work.
        if not hasattr(prefs, 'defaults') or not isinstance(prefs.defaults, dict):
            return prefs

        # Create a snapshot dict from defaults
        p = prefs.defaults.copy()
        for k in p:
            val = prefs.get(k, p[k])
            # If get() returns a mock, keep the default
            if hasattr(val, 'assert_called') or hasattr(val, 'return_value'):
                continue
            p[k] = val

        # Normalize legacy display strings to internal values
        if 'replace_vain_lord' in p:
            p['replace_vain_lord'] = _VAIN_MAP.get(p['replace_vain_lord'], p['replace_vain_lord'])
        if 'ass_mode' in p:
            p['ass_mode'] = _ASS_MAP.get(p['ass_mode'], p['ass_mode'])
        return p
    except ImportError:
        return {}


# ---------------------------------------------------------------------------
# Plugin metadata
# ---------------------------------------------------------------------------

class CleanerPlugin(InterfaceActionBase):
    name = 'Language Cleaner'
    description = 'Toolbar button to clean language in selected books'
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'Jordan Anderson'
    version = (2026, 5, 12)
    minimum_calibre_version = (5, 0, 0)
    actual_plugin = 'calibre_plugins.language_clean_plugin.action:CleanerAction'

    def is_customizable(self):
        return True

    def config_widget(self):
        from .config_widget import ConfigWidget
        return ConfigWidget()

    def save_settings(self, config_widget):
        config_widget.commit()


# ---------------------------------------------------------------------------
# Core cleaning logic
# ---------------------------------------------------------------------------

def _atomic_write(path, text, encoding):
    """Write text to a temporary file then rename to destination."""
    import shutil
    fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(path), suffix='.tmp')
    os.close(fd)
    try:
        with open(tmp_path, 'w', encoding=encoding) as f:
            f.write(text)
        shutil.move(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        raise


def _build_replacement_list(full_text, _p, log_fn):
    """
    Build the ordered list of (pattern, replacement, case_fn) tuples.
    Reads prefs snapshot _p; uses full_text only for auto-detection heuristics.
    """
    vain_raw = _p.get('replace_vain_lord', 'auto')
    ass_raw = _p.get('ass_mode', 'auto')

    replacement_list = language_check(
        full_text,
        vain_override=_VAIN_MAP.get(vain_raw, vain_raw),
        ass_override=_ASS_MAP.get(ass_raw, ass_raw),
        replace_slurs=_p.get('replace_slurs', True),
        replace_crude=_p.get('replace_crude', True),
        replace_damn=_p.get('replace_damn', True),
        replace_bitch=_p.get('replace_bitch', True),
        replace_shit=_p.get('replace_shit', True),
        replace_fbomb=_p.get('replace_fbomb', True),
        replace_hell=_p.get('replace_hell', True),
        replace_religious=_p.get('replace_religious', True),
        replace_ass=_p.get('replace_ass', True),
        replace_god=_p.get('replace_god', False),
    )

    for entry in _p.get('custom_replacements', []):
        if len(entry) < 2:
            log_fn('Custom replacement skipped — entry too short: %s' % str(entry))
            continue
        find, replace = entry[0], entry[1]
        ignore_case = entry[2] if len(entry) > 2 else True
        is_regex    = entry[3] if len(entry) > 3 else False
        flags = re.I if ignore_case else 0
        try:
            pattern = find if is_regex else re.escape(find)
            pat = re.compile(pattern, flags)
            # Regex replacements: literal sub() so backreferences (\1) expand.
            # Literal replacements: keep_case to preserve capitalisation.
            pcase_fn = False if is_regex else keep_case
            replacement_list.append((pat, replace, pcase_fn))
        except Exception as e:
            log_fn('Custom replacement "%s" skipped — invalid regex: %s' % (find, e))

    return replacement_list


# Strip HTML tags and decode common entities for visible-text comparison.
_TAG_RE    = re.compile(r'<[^>]+>')
_ENTITY_RE = re.compile(r'&[a-z]{2,6};|&#\d+;')


def _visible(s):
    """Return the visible text of an HTML snippet, stripped of tags and entities."""
    s = _TAG_RE.sub('', s)
    s = _ENTITY_RE.sub(' ', s)
    return s.strip()


def _collect_diffs(text, output, basename, diffs):
    """Append (filename, orig_visible, clean_visible) tuples for changed lines."""
    for orig_line, clean_line in zip(text.splitlines(), output.splitlines()):
        orig_v  = _visible(orig_line)
        clean_v = _visible(clean_line)
        if orig_v != clean_v and orig_v:
            diffs.append((basename, orig_v, clean_v))


def clean_ebook_file(path_to_ebook, log=None, dry_run=False, prefs_snapshot=None, title=None):
    """
    Clean (or dry-run preview) an ebook file in-place.

    Raises RuntimeError with a human-readable message on unpack/rebuild failure
    so callers (worker threads) can surface the error to the user.

    Returns:
      dry_run=False: (changes_made: bool, replacement_count: int)
      dry_run=True:  (changes_made: bool, diffs: list of (fname, orig, clean))
    """
    def _log(msg):
        (log.info if log else prints)(msg)

    fmt = path_to_ebook.rpartition('.')[-1].lower()
    try:
        exploder, rebuilder = get_tools(fmt)
    except (ValueError, KeyError):
        msg = 'Format %s is not supported for cleaning.' % fmt.upper()
        _log(msg)
        raise RuntimeError(msg)

    _p = prefs_snapshot if prefs_snapshot is not None else _load_prefs_direct()

    # Plain text / HTML files have no exploder or rebuilder in calibre's tweak
    # toolchain.  Handle them directly: read, clean, and write the file in-place
    # without any unpack/repack step.
    if exploder is None:
        return _clean_flat_file(path_to_ebook, fmt, _p, _log, dry_run, title=title)

    changes_made = False
    replacement_count = 0
    diffs = []
    tmppath = '_tweak_' + os.path.basename(path_to_ebook).rpartition('.')[0]

    with tempfile.TemporaryDirectory(prefix=tmppath) as tdir:
        opf_content = _unpack_ebook(path_to_ebook, exploder, tdir, _log)
        file_encodings, full_text = _collect_files(tdir, opf_content, fmt, _log)

        if not full_text:
            return (False, []) if dry_run else (False, 0)

        replacement_list = _build_replacement_list(full_text, _p, _log)
        if not replacement_list:
            return (False, []) if dry_run else (False, 0)

        from .cleaner import RuleEngine
        engine = RuleEngine(replacement_list)
        start_text = full_text
        end_text   = ''

        for f, enc in file_encodings.items():
            _log('Cleaning %s' % f)
            with open(f, 'r', encoding=enc) as fh:
                text = fh.read()

            ftype   = _get_ftype(f)
            is_html = bool(ftype and 'html' in ftype)

            if dry_run:
                # Line-by-line for dry-run: BS4 reformats the DOM on serialisation,
                # making zip(splitlines) pair wrong lines and produce garbage diffs.
                output, count = _clean_text_content(text, engine)
            elif is_html:
                output, count = clean_html_content(text, engine)
            else:
                output, count = _clean_text_content(text, engine)

            if output != text:
                changes_made = True
                replacement_count += count
                if dry_run:
                    _collect_diffs(text, output, os.path.basename(f), diffs)
                else:
                    with open(f, 'w', encoding=enc) as fh:
                        fh.write(output)

            end_text += output

        if dry_run:
            return changes_made, diffs

        if changes_made:
            _write_logs(path_to_ebook, start_text, end_text, _p, _log, title=title)
        else:
            _log('Language cleaner made no changes')

        _log('Rebuilding %s please wait ...' % path_to_ebook)
        try:
            rebuilder(tdir, path_to_ebook)
        except WorkerError as e:
            tb = getattr(e, 'orig_tb', None) or str(e)
            _log('Failed to rebuild %s' % path_to_ebook)
            _log(tb)
            raise RuntimeError('Failed to rebuild: %s' % tb) from e

    _log('%s successfully cleaned' % path_to_ebook)
    return changes_made, replacement_count


def _clean_flat_file(path_to_ebook, fmt, _p, _log, dry_run, title=None):
    """
    Clean a single flat file (HTML, TXT, ZIP, etc.) that has no calibre
    exploder/rebuilder.  For ZIP files, members are cleaned in-place inside
    a temp copy and then the original is replaced.  For plain text/HTML the
    file is read, cleaned, and written back directly.
    """
    if fmt == 'zip':
        return _clean_zip_file(path_to_ebook, _p, _log, dry_run, title=title)

    try:
        text, enc = read_file_with_encoding(path_to_ebook)
    except UnicodeDecodeError as e:
        raise RuntimeError('Could not read %s: %s' % (path_to_ebook, e)) from e

    replacement_list = _build_replacement_list(text, _p, _log)
    if not replacement_list:
        return (False, []) if dry_run else (False, 0)

    from .cleaner import RuleEngine
    engine = RuleEngine(replacement_list)
    ftype   = _get_ftype(path_to_ebook)
    is_html = bool(ftype and 'html' in ftype)
    basename = os.path.basename(path_to_ebook)

    if dry_run:
        output, _count = _clean_text_content(text, engine)
        if output == text:
            return False, []
        diffs = []
        _collect_diffs(text, output, basename, diffs)
        return True, diffs

    if is_html:
        output, count = clean_html_content(text, engine)
    else:
        output, count = _clean_text_content(text, engine)

    if output == text:
        _log('Language cleaner made no changes')
        return False, 0

    _write_logs(path_to_ebook, text, output, _p, _log, title=title)
    _atomic_write(path_to_ebook, output, enc)
    _log('%s successfully cleaned' % path_to_ebook)
    return True, count


def _clean_zip_file(path_to_ebook, _p, _log, dry_run, title=None):
    """
    Clean text/HTML members inside a ZIP file (calibre\'s raw ZIP book format).
    Images, fonts, CSS, and other binary members are left completely untouched.
    The ZIP is rebuilt in-place only when changes are actually made.
    """
    if not zipfile.is_zipfile(path_to_ebook):
        raise RuntimeError('%s is not a valid ZIP file.' % os.path.basename(path_to_ebook))

    # Read all members up front so we can detect changes before writing
    try:
        with zipfile.ZipFile(path_to_ebook, 'r') as zin:
            names    = zin.namelist()
            raw_data = {name: zin.read(name) for name in names}
            infos    = {info.filename: info for info in zin.infolist()}
    except zipfile.BadZipFile as e:
        raise RuntimeError('Could not open ZIP %s: %s' % (os.path.basename(path_to_ebook), e)) from e

    # Build replacement engine from the combined text of all processable members
    start_text = ''
    member_encodings = {}
    for name in names:
        ftype = _get_ftype(name)
        if ftype and ('html' in ftype or 'text' in ftype):
            text, enc = _decode_bytes(raw_data[name])
            if text is not None:
                start_text += text
                member_encodings[name] = enc
            else:
                _log('Skipping member %s — unknown encoding' % name)

    if not start_text:
        return (False, []) if dry_run else (False, 0)

    replacement_list = _build_replacement_list(start_text, _p, _log)
    if not replacement_list:
        return (False, []) if dry_run else (False, 0)

    from .cleaner import RuleEngine
    engine = RuleEngine(replacement_list)
    changes_made = False
    total_count = 0
    diffs = []
    cleaned_data = {}   # name -> bytes, only for changed members
    end_text = ''

    for name in names:
        if name not in member_encodings:
            continue

        enc  = member_encodings[name]
        raw  = raw_data[name]
        text, _ = _decode_bytes(raw)
        # text will not be None because we validated it in the first pass

        is_html = 'html' in _get_ftype(name)
        if dry_run:
            output, _count = _clean_text_content(text, engine)
            if output != text:
                changes_made = True
                _collect_diffs(text, output, name, diffs)
        else:
            if is_html:
                output, count = clean_html_content(text, engine)
            else:
                output, count = _clean_text_content(text, engine)

            if output != text:
                changes_made = True
                total_count += count
                cleaned_data[name] = output.encode(enc)
                _log('Cleaned ZIP member: %s' % name)

            end_text += output

    if dry_run:
        return changes_made, diffs

    if not changes_made:
        _log('Language cleaner made no changes')
        return False, 0

    _write_logs(path_to_ebook, start_text, end_text, _p, _log, title=title)

    # Rewrite the ZIP in-place using a temp file then atomic replace
    fd, tmp_path = tempfile.mkstemp(suffix='.zip', dir=os.path.dirname(path_to_ebook))
    os.close(fd)
    try:
        with zipfile.ZipFile(path_to_ebook, 'r') as zin, \
             zipfile.ZipFile(tmp_path, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
            for name in names:
                info = infos[name]
                if name in cleaned_data:
                    zout.writestr(info, cleaned_data[name])
                else:
                    zout.writestr(info, raw_data[name])
        os.replace(tmp_path, path_to_ebook)
    except Exception as e:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise RuntimeError('Failed to rewrite ZIP %s: %s' % (os.path.basename(path_to_ebook), e)) from e

    _log('%s successfully cleaned (%d replacement(s))' % (path_to_ebook, total_count))
    return True, total_count


def _unpack_ebook(ebook_file, exploder, tdir, log_fn):
    """
    Unpack the ebook into tdir; return OPF content string (may be empty).
    Raises RuntimeError with a user-readable message on failure.
    """
    try:
        opf_path = exploder(ebook_file, tdir)
        if opf_path and os.path.exists(opf_path):
            with open(opf_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        return ''
    except WorkerError as e:
        tb = getattr(e, 'orig_tb', None) or str(e)
        log_fn('Failed to unpack %s' % ebook_file)
        log_fn(tb)
        raise RuntimeError(tb) from e
    except Error as e:
        msg = str(e)
        log_fn('Error unpacking %s: %s' % (ebook_file, msg))
        raise RuntimeError(msg) from e


def _collect_files(tdir, opf_content, fmt, log_fn):
    """
    Walk tdir; return (file_encodings dict, concatenated full_text).
    Only processes files referenced in the OPF manifest (or all files for txt).
    """
    opf_lines = opf_content.split('\n')
    file_encodings = {}
    full_text = ''

    def _should_process(f):
        ftype = _get_ftype(f)
        if not ftype or ('text' not in ftype and 'html' not in ftype):
            return False
        # HTMLZ files are zips that often have an index.html and other text files.
        # TXT files have no OPF.
        filename = os.path.basename(f)
        # Proper word-boundary check to avoid partial matches (e.g. "a.html" matching "extra.html")
        pattern = r'\b' + re.escape(filename.lower()) + r'\b'
        in_opf = any(re.search(pattern, line.lower()) for line in opf_lines)
        return in_opf or fmt in ('txt', 'htmlz') or not opf_content

    for f in _walk(tdir):
        if _should_process(f):
            try:
                content, enc = read_file_with_encoding(f)
                full_text += content
                file_encodings[f] = enc
            except UnicodeDecodeError:
                log_fn('Failed to read %s with any encoding' % f)

    return file_encodings, full_text


def _write_logs(ebook_file, start_text, end_text, _p, log_fn, title=None):
    """Write before/after log files if logging is enabled."""
    try:
        logdir = _get_logdir(_p)
        if not logdir:
            return
        ts   = time.strftime('%Y%m%d_%H%M%S')
        if title:
            # Simple sanitization for filesystem safety
            base = re.sub(r'[\\/*?:"<>|]', '_', title)
        else:
            base = os.path.basename(ebook_file)
        for suffix, text in (('init', start_text), ('mod', end_text)):
            path = os.path.join(logdir, '%s_%s_%s.txt' % (base, ts, suffix))
            with open(path, 'w', encoding='utf-8') as f:
                f.write(text)
    except Exception as e:
        log_fn('Failed to write logs: %s' % e)
