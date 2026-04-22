import unittest
import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch
import sys
import types
import importlib
import importlib.util

# Detailed mock setup for calibre package
calibre = types.ModuleType('calibre')
calibre.__path__ = []
sys.modules['calibre'] = calibre

utils = types.ModuleType('calibre.utils')
utils.__path__ = []
calibre.utils = utils
sys.modules['calibre.utils'] = utils

config_mod = MagicMock()
utils.config = config_mod
sys.modules['calibre.utils.config'] = config_mod

logging_mod = MagicMock()
utils.logging = logging_mod
sys.modules['calibre.utils.logging'] = logging_mod

ebooks = types.ModuleType('calibre.ebooks')
ebooks.__path__ = []
calibre.ebooks = ebooks
sys.modules['calibre.ebooks'] = ebooks

tweak = MagicMock()
ebooks.tweak = tweak
sys.modules['calibre.ebooks.tweak'] = tweak

class BaseMock:
    def __init__(self, *args, **kwargs):
        pass

customize = types.ModuleType('calibre.customize')
calibre.customize = customize
sys.modules['calibre.customize'] = customize
customize.InterfaceActionBase = BaseMock
customize.FileTypePlugin = BaseMock

gui2 = types.ModuleType('calibre.gui2')
gui2.__path__ = []
calibre.gui2 = gui2
sys.modules['calibre.gui2'] = gui2
gui2.error_dialog = MagicMock()
gui2.info_dialog = MagicMock()
gui2.question_dialog = MagicMock()
gui2.Dispatcher = MagicMock()
gui2.gprefs = MagicMock()
gui2.threaded_jobs = MagicMock()
sys.modules['calibre.gui2.threaded_jobs'] = gui2.threaded_jobs
gui2.threaded_jobs.ThreadedJob = MagicMock()

actions = types.ModuleType('calibre.gui2.actions')
actions.__path__ = []
gui2.actions = actions
sys.modules['calibre.gui2.actions'] = actions
actions.InterfaceAction = BaseMock

ptempfile = MagicMock()
calibre.ptempfile = ptempfile
sys.modules['calibre.ptempfile'] = ptempfile

# Define real exception classes for tweak
class FakeWorkerError(Exception):
    def __init__(self, msg, orig_tb=None):
        super().__init__(msg)
        self.orig_tb = orig_tb

class FakeError(Exception):
    pass

tweak.WorkerError = FakeWorkerError
tweak.Error = FakeError

# Minimal PyQt5 mock (action.py imports QTimer at module level)
class _MockQTimer:
    @staticmethod
    def singleShot(ms, fn): pass

_pyqt5_mock = MagicMock()
_pyqt5_qt_mock = MagicMock()
_pyqt5_qt_mock.QTimer = _MockQTimer
sys.modules['PyQt5'] = _pyqt5_mock
sys.modules['PyQt5.Qt'] = _pyqt5_qt_mock

# ---------------------------------------------------------------------------
# Bootstrap the calibre_plugins.language_clean_plugin namespace so that
# relative imports inside the plugin modules resolve to the project directory.
# ---------------------------------------------------------------------------
_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

_cp_pkg = types.ModuleType('calibre_plugins')
_cp_pkg.__path__ = [_PROJECT_DIR]
_cp_pkg.__package__ = 'calibre_plugins'
sys.modules['calibre_plugins'] = _cp_pkg

_plugin_pkg = types.ModuleType('calibre_plugins.language_clean_plugin')
_plugin_pkg.__path__ = [_PROJECT_DIR]
_plugin_pkg.__package__ = 'calibre_plugins.language_clean_plugin'
sys.modules['calibre_plugins.language_clean_plugin'] = _plugin_pkg

# Execute __init__.py into the package NOW so CleanerPlugin is available
# when action.py imports it at module level.
_init_spec = importlib.util.spec_from_file_location(
    'calibre_plugins.language_clean_plugin',
    os.path.join(_PROJECT_DIR, '__init__.py'),
)
_init_spec.loader.exec_module(_plugin_pkg)

def load_plugin_mod(name):
    full_name = f'calibre_plugins.language_clean_plugin.{name}'
    if full_name in sys.modules:
        del sys.modules[full_name]
    spec = importlib.util.spec_from_file_location(
        full_name,
        os.path.join(_PROJECT_DIR, f'{name}.py'),
    )
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = 'calibre_plugins.language_clean_plugin'
    sys.modules[full_name] = mod
    spec.loader.exec_module(mod)
    return mod

cleaner = load_plugin_mod('cleaner')
config_plugin = load_plugin_mod('config')
action = load_plugin_mod('action')

_init_spec = importlib.util.spec_from_file_location(
    'calibre_plugins.language_clean_plugin',
    os.path.join(_PROJECT_DIR, '__init__.py'),
)
_init_spec.loader.exec_module(_plugin_pkg)
plugin = _plugin_pkg

class TestPlugin(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_read_file_with_encoding(self):
        f = os.path.join(self.test_dir, 'test.txt')
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write('hello world')
        content, enc = plugin.read_file_with_encoding(f)
        self.assertEqual(content, 'hello world')
        self.assertEqual(enc, 'utf-8')

        with open(f, 'w', encoding='windows-1252') as fh:
            fh.write('héllo')
        content, enc = plugin.read_file_with_encoding(f)
        self.assertEqual(content, 'héllo')
        self.assertEqual(enc, 'windows-1252')

        with open(f, 'wb') as fh:
            fh.write(b'\x81')
        with self.assertRaises(UnicodeDecodeError):
            plugin.read_file_with_encoding(f)

    def test_get_ftype(self):
        self.assertEqual(plugin._get_ftype('test.html'), 'text/html')
        self.assertIn(plugin._get_ftype('test.xhtml'), ('text/html', 'application/xhtml+xml'))

    @patch('calibre_plugins.language_clean_plugin.config.prefs')
    def test_get_logdir(self, mock_prefs):
        # write_log=True, no custom dir → returns default path
        def _prefs_get(key, default=None):
            if key == 'write_log': return True
            if key == 'log_dir': return ''
            return default
        mock_prefs.get.side_effect = _prefs_get
        import calibre.utils.config
        with patch.object(calibre.utils.config, 'config_dir', '/tmp/calibre_config'),              patch('calibre_plugins.language_clean_plugin.os.makedirs'),              patch('calibre_plugins.language_clean_plugin.os.path.isdir', return_value=False):
            self.assertEqual(plugin._get_logdir(), '/tmp/calibre_config/language_cleaner_logs')

        # write_log=False → None
        mock_prefs.get.side_effect = None
        mock_prefs.get.return_value = False
        self.assertIsNone(plugin._get_logdir())

        # write_log=True, custom dir set and exists → returns custom dir
        def _prefs_custom(key, default=None):
            if key == 'write_log': return True
            if key == 'log_dir': return '/my/logs'
            return default
        mock_prefs.get.side_effect = _prefs_custom
        with patch('calibre_plugins.language_clean_plugin.os.path.isdir', return_value=True):
            self.assertEqual(plugin._get_logdir(), '/my/logs')

    @patch('calibre_plugins.language_clean_plugin.get_tools')
    @patch('calibre_plugins.language_clean_plugin.tempfile.TemporaryDirectory')
    @patch('calibre_plugins.language_clean_plugin._unpack_ebook')
    @patch('calibre_plugins.language_clean_plugin._collect_files')
    @patch('calibre_plugins.language_clean_plugin._build_replacement_list')
    @patch('calibre_plugins.language_clean_plugin._get_logdir')
    def test_clean_ebook_file(self, mock_logdir, mock_build, mock_collect,
                              mock_unpack, mock_tdir, mock_tools):
        """clean_ebook_file: verifies normal and dry-run paths."""
        mock_exploder = MagicMock()
        mock_rebuilder = MagicMock()
        mock_tools.return_value = (mock_exploder, mock_rebuilder)
        mock_tdir.return_value.__enter__.return_value = self.test_dir

        content_path = os.path.join(self.test_dir, 'content.html')
        with open(content_path, 'w', encoding='utf-8') as f:
            f.write('<html><body>shit</body></html>')

        mock_unpack.return_value = 'content.html'
        mock_collect.return_value = (
            {content_path: 'utf-8'},
            '<html><body>shit</body></html>',
        )
        mock_build.return_value = cleaner.re_list
        mock_logdir.return_value = None

        # 1. Normal run — file is modified, (True, count) returned
        res, count = plugin.clean_ebook_file('test.epub')
        self.assertTrue(res)
        self.assertGreater(count, 0)

        # 2. Dry-run — file unchanged, diffs returned
        with open(content_path, 'w', encoding='utf-8') as f:
            f.write('<html><body>shit</body></html>')
        res, diffs = plugin.clean_ebook_file('test.epub', dry_run=True)
        self.assertTrue(res)
        self.assertTrue(len(diffs) > 0)

    @patch('calibre_plugins.language_clean_plugin.get_tools')
    def test_clean_ebook_file_unsupported_format(self, mock_tools):
        """Unsupported format raises RuntimeError (not silent return)."""
        mock_tools.side_effect = ValueError('unsupported')
        with self.assertRaises(RuntimeError) as ctx:
            plugin.clean_ebook_file('test.xyz')
        self.assertIn('XYZ', str(ctx.exception))

    @patch('calibre_plugins.language_clean_plugin.get_tools')
    @patch('calibre_plugins.language_clean_plugin._build_replacement_list')
    def test_clean_flat_file_html_normal(self, mock_build, mock_tools):
        """clean_ebook_file with None exploder (plain HTML) cleans in-place."""
        mock_tools.return_value = (None, None)
        mock_build.return_value = cleaner.re_list

        html_path = os.path.join(self.test_dir, 'book.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write('<html><body>shit</body></html>')

        res, count = plugin.clean_ebook_file(html_path)
        self.assertTrue(res)
        self.assertGreater(count, 0)
        with open(html_path, encoding='utf-8') as f:
            content = f.read()
        self.assertNotIn('shit', content)

    @patch('calibre_plugins.language_clean_plugin.get_tools')
    @patch('calibre_plugins.language_clean_plugin._build_replacement_list')
    def test_clean_flat_file_html_dry_run(self, mock_build, mock_tools):
        """dry_run=True with None exploder returns diffs without writing file."""
        mock_tools.return_value = (None, None)
        mock_build.return_value = cleaner.re_list

        original = '<html><body>shit</body></html>'
        html_path = os.path.join(self.test_dir, 'book.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(original)

        changed, diffs = plugin.clean_ebook_file(html_path, dry_run=True)
        self.assertTrue(changed)
        self.assertGreater(len(diffs), 0)
        # File must NOT be modified during dry-run
        with open(html_path, encoding='utf-8') as f:
            self.assertEqual(f.read(), original)

    @patch('calibre_plugins.language_clean_plugin.get_tools')
    @patch('calibre_plugins.language_clean_plugin._build_replacement_list')
    def test_clean_flat_file_no_changes(self, mock_build, mock_tools):
        """_clean_flat_file returns (False, 0) when text is already clean."""
        mock_tools.return_value = (None, None)
        mock_build.return_value = cleaner.re_list

        html_path = os.path.join(self.test_dir, 'clean.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write('<html><body>Hello world</body></html>')

        res, count = plugin.clean_ebook_file(html_path)
        self.assertFalse(res)
        self.assertEqual(count, 0)

    @patch('calibre_plugins.language_clean_plugin.get_tools')
    @patch('calibre_plugins.language_clean_plugin._build_replacement_list')
    def test_clean_flat_file_txt(self, mock_build, mock_tools):
        """_clean_flat_file works on plain .txt files too."""
        mock_tools.return_value = (None, None)
        mock_build.return_value = cleaner.re_list

        txt_path = os.path.join(self.test_dir, 'book.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write('That damn nuisance.')

        res, count = plugin.clean_ebook_file(txt_path)
        self.assertTrue(res)
        with open(txt_path, encoding='utf-8') as f:
            content = f.read()
        self.assertNotIn('damn', content)


    def test_worker_clean_logs_diffs(self):
        """_worker_clean logs before/after lines for each change when diffs exist.
        The dry-run pass must use log=None so 'Cleaning ...' file lines are not
        emitted to the job log."""
        import threading
        import queue as _queue

        html_path = os.path.join(self.test_dir, 'book.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write('<html><body>This is shit.</body></html>')

        work_items = [dict(book_id=1, title='Test Book', fmt='html', path=html_path)]
        prefs_snapshot = {
            'replace_slurs': True, 'replace_crude': True, 'replace_damn': True,
            'replace_bitch': True, 'replace_shit': True, 'replace_fbomb': True,
            'replace_hell': True, 'replace_religious': True, 'replace_vain_lord': 'auto',
            'ass_mode': 'auto', 'replace_ass': True, 'replace_god': False,
            'custom_replacements': [], 'write_log': False, 'log_dir': '',
        }

        fake_diffs = [('book.html', 'This is shit.', 'This is trash.')]
        calls = []

        def _fake_clean(path, log=None, dry_run=False, prefs_snapshot=None, title=None):
            calls.append(dict(log=log, dry_run=dry_run))
            if dry_run:
                return True, fake_diffs
            return True, 1

        log = MagicMock()
        abort = threading.Event()
        notifications = _queue.Queue()

        with patch('calibre_plugins.language_clean_plugin.clean_ebook_file',
                   side_effect=_fake_clean):
            action._worker_clean(work_items, prefs_snapshot, abort, log, notifications)

        # Dry-run must have been called with log=None (no "Cleaning ..." noise)
        dry_calls = [c for c in calls if c['dry_run']]
        self.assertEqual(len(dry_calls), 1, 'Expected exactly one dry-run call')
        self.assertIsNone(dry_calls[0]['log'],
                          'Dry-run must pass log=None to suppress file-level noise')

        logged = [c.args[0] for c in log.info.call_args_list]

        # Diff lines must appear in the job log
        minus_lines = [l for l in logged if l.startswith('      - ')]
        plus_lines  = [l for l in logged if l.startswith('      + ')]
        self.assertTrue(minus_lines, 'Expected "      - <orig>" lines in log')
        self.assertTrue(plus_lines,  'Expected "      + <clean>" lines in log')
        self.assertTrue(any('shit' in l for l in minus_lines))
        self.assertTrue(any('trash' in l for l in plus_lines))

        # Filename header line must be present
        file_lines = [l for l in logged if 'book.html' in l and l.strip().startswith('[')]
        self.assertTrue(file_lines, 'Expected filename header line in log')

        # Count summary must appear
        self.assertTrue(any('1 replacement' in l for l in logged),
                        'Expected replacement count summary in log')

    def test_clean_html_content(self):
        engine = cleaner.RuleEngine(cleaner.re_list)
        html = '<html><body><p>This is shit.</p><script>var shit = 1;</script></body></html>'
        cleaned, count = plugin.clean_html_content(html, engine)
        self.assertIn('This is trash.', cleaned)
        self.assertIn('var shit = 1;', cleaned)
        self.assertEqual(count, 1)

    def test_clean_text_content(self):
        engine = cleaner.RuleEngine(cleaner.re_list)
        text = 'This is shit.\nAnother shit.'
        cleaned, count = plugin._clean_text_content(text, engine)
        self.assertEqual(cleaned, 'This is trash.\nAnother trash.')
        self.assertEqual(count, 2)

if __name__ == '__main__':
    unittest.main()
