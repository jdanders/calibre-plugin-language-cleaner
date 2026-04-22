import unittest
import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch, call
import sys
import types
import importlib

class BaseMock:
    def __init__(self, *args, **kwargs):
        if len(args) >= 1: self.gui = args[0]
        if len(args) >= 2: self.name = args[1]
    def create_menu_action(self, *args, **kwargs):
        pass

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

# Mock PyQt5/qt.core
if 'qt.core' not in sys.modules:
    sys.modules['qt.core'] = MagicMock()
if 'PyQt5' not in sys.modules:
    sys.modules['PyQt5'] = MagicMock()
    sys.modules['PyQt5.Qt'] = MagicMock()

# Bootstrap plugin namespace
_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
_cp_pkg = types.ModuleType('calibre_plugins')
_cp_pkg.__path__ = [_PROJECT_DIR]
_cp_pkg.__package__ = 'calibre_plugins'
sys.modules['calibre_plugins'] = _cp_pkg
_plugin_pkg = types.ModuleType('calibre_plugins.language_clean_plugin')
_plugin_pkg.__path__ = [_PROJECT_DIR]
_plugin_pkg.__package__ = 'calibre_plugins.language_clean_plugin'
sys.modules['calibre_plugins.language_clean_plugin'] = _plugin_pkg

def load_plugin_mod(name):
    full_name = f'calibre_plugins.language_clean_plugin.{name}'
    if full_name in sys.modules:
        del sys.modules[full_name]
    spec = importlib.util.spec_from_file_location(full_name, os.path.join(_PROJECT_DIR, f'{name}.py'))
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = 'calibre_plugins.language_clean_plugin'
    sys.modules[full_name] = mod
    spec.loader.exec_module(mod)
    return mod

cleaner = load_plugin_mod('cleaner')

_init_spec = importlib.util.spec_from_file_location(
    'calibre_plugins.language_clean_plugin',
    os.path.join(_PROJECT_DIR, '__init__.py'),
)
_init_spec.loader.exec_module(_plugin_pkg)

config_mod = load_plugin_mod('config')
action_mod = load_plugin_mod('action')

from calibre_plugins.language_clean_plugin.action import (
    _pick_format, CleanerAction, _worker_clean, _worker_preview
)

class TestActionExtended(unittest.TestCase):
    def setUp(self):
        self.gui = MagicMock()
        self.action = CleanerAction(self.gui, 'Language Cleaner')
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_pick_format(self):
        # Preference order: epub, azw3, mobi, htmlz, zip, html, txt
        self.assertEqual(_pick_format(['MOBI', 'EPUB']), 'epub')
        self.assertEqual(_pick_format(['AZW3', 'MOBI']), 'azw3')
        self.assertEqual(_pick_format(['TXT', 'HTML']), 'html')
        self.assertEqual(_pick_format(['UNKNOWN']), 'unknown')
        self.assertIsNone(_pick_format([]))

    def test_on_clean_complete_with_backup(self):
        job = MagicMock()
        job.failed = False
        job.result = [
            {'book_id': 1, 'title': 'Book 1', 'fmt': 'epub', 'path': '/tmp/1.epub', 'changes_made': True}
        ]
        
        db = MagicMock()
        self.gui.current_db.new_api = db
        
        with patch('calibre_plugins.language_clean_plugin.config.prefs.get', return_value=True), \
             patch('os.path.exists', return_value=True), \
             patch('os.remove'):
            self.action._on_clean_complete(job)
            
            db.save_original_format.assert_called_with(1, 'EPUB')
            db.add_format.assert_called()

    def test_on_preview_complete_failed(self):
        job = MagicMock()
        job.failed = True
        job.details = 'Some error'
        job.args = [{'path': '/tmp/test.epub'}]
        
        with patch('os.path.exists', return_value=True), patch('os.remove'), \
             patch('calibre_plugins.language_clean_plugin.action.error_dialog') as mock_err:
            self.action._on_preview_complete(job)
            mock_err.assert_called()
            self.assertIn('failed unexpectedly', mock_err.call_args[0][2])

    def test_on_preview_complete_no_changes(self):
        job = MagicMock()
        job.failed = False
        job.result = {'title': 'Book 1', 'changes': [], 'error': None}
        job.args = [{'path': '/tmp/test.epub'}]
        
        with patch('os.path.exists', return_value=True), patch('os.remove'), \
             patch('calibre_plugins.language_clean_plugin.action.info_dialog') as mock_info:
            self.action._on_preview_complete(job)
            mock_info.assert_called()
            self.assertIn('No changes', mock_info.call_args[0][2])

    def test_on_preview_complete_with_changes(self):
        job = MagicMock()
        job.failed = False
        job.result = {'title': 'Book 1', 'changes': [('f1.html', 'shit', 'rubbish')], 'error': None}
        job.args = [{'path': '/tmp/test.epub'}]
        
        with patch('os.path.exists', return_value=True), patch('os.remove'), \
             patch.object(self.action, '_show_diff_dialog') as mock_diff:
            self.action._on_preview_complete(job)
            mock_diff.assert_called_with([('f1.html', 'shit', 'rubbish')])

    def test_mark_changed_words(self):
        # Basic replacement
        res = self.action._mark_changed_words("Hello shit world", "Hello rubbish world")
        self.assertIn('<b', res)
        self.assertIn('shit', res)
        
        # Multiple words, punctuation
        res = self.action._mark_changed_words("One, two, three!", "One, four, three!")
        self.assertIn('two', res)
        self.assertIn('<b', res)

    def test_is_on_any_toolbar_fallback(self):
        self.gui.bars_manager.bars = []
        self.gui.bars_manager.menu_bar.actions.return_value = []
        
        from calibre.gui2 import gprefs
        with patch.object(gprefs, 'get') as mock_gprefs:
            mock_gprefs.return_value = ['Other Action', 'Language Cleaner']
            self.assertTrue(self.action.is_on_any_toolbar())
            
            mock_gprefs.return_value = ['Other Action']
            self.assertFalse(self.action.is_on_any_toolbar())

    def test_is_in_context_menu_fallback(self):
        del self.gui.library_view.context_menu
        
        with patch('calibre_plugins.language_clean_plugin.action.gprefs.get') as mock_gprefs:
            mock_gprefs.return_value = ['Language Cleaner']
            self.action.name = 'Language Cleaner'
            res = self.action.is_in_context_menu()
            self.assertTrue(res)

    def test_show_setup_instructions(self):
        with patch('calibre_plugins.language_clean_plugin.action.QDialog') as mock_dialog:
            with patch('calibre_plugins.language_clean_plugin.action.QLabel') as mock_label:
                self.action.show_setup_instructions(True, True)
                mock_dialog.assert_called()
                label_text = mock_label.call_args[0][0]
                self.assertIn('toolbar', label_text)
                self.assertIn('right-click menu', label_text)

    def test_choose_format_cancelled(self):
        with patch('calibre_plugins.language_clean_plugin.action.ChooseFormatDialog') as mock_dialog:
            mock_dialog.return_value.exec_.return_value = False
            res = self.action._choose_format(['epub', 'mobi'], 'Title')
            self.assertIsNone(res)

    def test_choose_format_fallback(self):
        with patch('calibre_plugins.language_clean_plugin.action.ChooseFormatDialog', None):
            res = self.action._choose_format(['mobi', 'epub'], 'Title')
            self.assertEqual(res, 'epub') # best format auto-picked

    def test_clean_selected_books_multi_format_hint(self):
        rows = [MagicMock()]
        self.gui.library_view.selectionModel().selectedRows.return_value = rows
        self.gui.library_view.get_selected_ids.return_value = [1, 2]
        
        db = MagicMock()
        self.gui.current_db.new_api = db
        db.field_for.side_effect = lambda f, id: f"Book {id}"
        db.formats.side_effect = lambda id: ['EPUB', 'AZW3'] if id == 2 else ['EPUB']
        
        with patch('calibre_plugins.language_clean_plugin.action.question_dialog') as mock_quest, \
             patch.object(self.action, '_snapshot_prefs', return_value={'show_confirm_dialog': True}):
            mock_quest.return_value = False # Cancel so we don't start the job
            self.action.clean_selected_books()
            
            msg = mock_quest.call_args[0][2]
            self.assertIn('Book 1', msg)
            self.assertIn('Book 2 [EPUB]', msg) # EPUB is best format

    def test_clean_selected_books_export_errors(self):
        rows = [MagicMock()]
        self.gui.library_view.selectionModel().selectedRows.return_value = rows
        self.gui.library_view.get_selected_ids.return_value = [1]
        
        db = MagicMock()
        self.gui.current_db.new_api = db
        db.field_for.return_value = "Broken Book"
        
        with patch.object(self.action, '_snapshot_prefs', return_value={'show_confirm_dialog': False}), \
             patch.object(self.action, '_export_book', side_effect=Exception("Export failed")), \
             patch('calibre_plugins.language_clean_plugin.action.error_dialog') as mock_err:
            self.action.clean_selected_books()
            mock_err.assert_called()
            self.assertIn('Broken Book', mock_err.call_args[0][2])
            self.assertIn('Export failed', mock_err.call_args[0][2])

    def test_worker_clean(self):
        work_items = [
            {'book_id': 1, 'title': 'Book 1', 'fmt': 'epub', 'path': os.path.join(self.test_dir, '1.epub')}
        ]
        with open(work_items[0]['path'], 'w') as f: f.write('shit')
        
        abort = MagicMock()
        abort.is_set.return_value = False
        log = MagicMock()
        notifications = MagicMock()
        
        # We need to mock clean_ebook_file because it's imported inside the worker
        with patch('calibre_plugins.language_clean_plugin.clean_ebook_file') as mock_clean:
            mock_clean.side_effect = [
                (True, [('f1.html', 'shit', 'rubbish')]), # dry_run=True call
                (True, 1) # dry_run=False call
            ]
            res = _worker_clean(work_items, {}, abort, log, notifications)
            self.assertEqual(res[0]['count'], 1)
            self.assertTrue(res[0]['changes_made'])

    def test_worker_clean_abort(self):
        work_items = [{'title': 'B1', 'path': 'p1', 'fmt': 'epub'}, {'title': 'B2', 'path': 'p2', 'fmt': 'epub'}]
        abort = MagicMock()
        abort.is_set.side_effect = [False, True]
        log = MagicMock()
        notifications = MagicMock()
        
        with patch('calibre_plugins.language_clean_plugin.clean_ebook_file', return_value=(True, 1)):
            res = _worker_clean(work_items, {}, abort, log, notifications)
            self.assertEqual(res[1]['error'], 'Aborted')

    def test_worker_preview(self):
        item = {'title': 'B1', 'fmt': 'epub', 'path': 'p1'}
        abort = MagicMock()
        log = MagicMock()
        notifications = MagicMock()
        
        with patch('calibre_plugins.language_clean_plugin.clean_ebook_file') as mock_clean:
            mock_clean.return_value = (True, [('f1.html', 'shit', 'rubbish')])
            res = _worker_preview(item, {}, abort, log, notifications)
            self.assertEqual(len(res['changes']), 1)
            self.assertEqual(res['title'], 'B1')

    def test_worker_preview_error(self):
        item = {'title': 'B1', 'fmt': 'epub', 'path': 'p1'}
        with patch('calibre_plugins.language_clean_plugin.clean_ebook_file', side_effect=Exception("Preview failed")):
            res = _worker_preview(item, {}, MagicMock(), MagicMock(), MagicMock())
            self.assertEqual(res['error'], 'Preview failed')

    def test_show_diff_dialog(self):
        changes = [('f1.html', 'shit', 'rubbish'), ('f2.html', 'damn', 'dang')]
        with patch('calibre_plugins.language_clean_plugin.action.QDialog'), \
             patch('calibre_plugins.language_clean_plugin.action.QVBoxLayout'), \
             patch('calibre_plugins.language_clean_plugin.action.QLabel'), \
             patch('calibre_plugins.language_clean_plugin.action.QTextEdit') as mock_edit, \
             patch('calibre_plugins.language_clean_plugin.action.QDialogButtonBox'):
            self.action._show_diff_dialog(changes)
            mock_edit.return_value.setHtml.assert_called()
            html_content = mock_edit.return_value.setHtml.call_args[0][0]
            self.assertIn('f1.html', html_content)
            self.assertIn('f2.html', html_content)
            self.assertIn('shit', html_content)

if __name__ == '__main__':
    unittest.main()
