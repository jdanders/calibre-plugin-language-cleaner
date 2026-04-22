import unittest
from unittest.mock import MagicMock, patch, call
import sys
import os
import types
import importlib

class BaseMock:
    def __init__(self, *args, **kwargs):
        # Calibre's InterfaceAction often gets a gui and name
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

ptempfile = MagicMock()
calibre.ptempfile = ptempfile
sys.modules['calibre.ptempfile'] = ptempfile

# Mock PyQt5.Qt
class MockQt:
    class QWidget:
        def __init__(self, *args, **kwargs): pass
        def setLayout(self, l): self.layout = l
        def rowCount(self): return 0
        def setMinimumWidth(self, w): pass
        def setMinimumHeight(self, h): pass
    class QVBoxLayout:
        def __init__(self, *args, **kwargs): pass
        def addWidget(self, w): pass
        def addLayout(self, l): pass
    class QHBoxLayout:
        def __init__(self, *args, **kwargs): pass
        def addWidget(self, w): pass
        def addLayout(self, l): pass
        def setContentsMargins(self, *args): pass
    class QCheckBox:
        def __init__(self, *args, **kwargs): pass
        def setChecked(self, v): pass
        def isChecked(self): return False
    class QComboBox:
        def __init__(self, *args, **kwargs): pass
        def addItems(self, items): pass
        def setCurrentText(self, t): pass
        def currentText(self): return ""
    class QTableWidget:
        def __init__(self, *args, **kwargs): pass
        def setColumnCount(self, c): pass
        def setHorizontalHeaderLabels(self, l): pass
        def horizontalHeader(self): return MagicMock()
        def insertRow(self, r): pass
        def setItem(self, r, c, i): pass
        def setCellWidget(self, r, c, w): pass
        def rowCount(self): return 0
    class QTableWidgetItem:
        def __init__(self, *args, **kwargs): pass
        def text(self): return ""
    class QPushButton:
        def __init__(self, *args, **kwargs):
            self.clicked = MagicMock()
    class Qt:
        WindowStaysOnTopHint = 0x00040000
    class QTimer:
        @staticmethod
        def singleShot(ms, fn): pass
    class QHeaderView:
        Stretch = 1
    class QLabel:
        def __init__(self, *args, **kwargs): pass
        def setWordWrap(self, v): pass
        def setOpenExternalLinks(self, v): pass
    class QLineEdit:
        def __init__(self, *args, **kwargs):
            self.returnPressed = MagicMock()
            self.setReadOnly = MagicMock()
        def setText(self, t): pass
        def text(self): return ''
        def setPlaceholderText(self, t): pass
    class QColor:
        def __init__(self, *args, **kwargs): pass
    class QFileDialog:
        @staticmethod
        def getExistingDirectory(*args, **kwargs): return ''
    class QIcon:
        def __init__(self, *args, **kwargs): pass
    class QPixmap:
        def __init__(self, *args, **kwargs): pass
        def loadFromData(self, d): pass
    class QMenu:
        def __init__(self, *args, **kwargs): pass
        def addAction(self, *args, **kwargs): pass
    class QDialog:
        def __init__(self, *args, **kwargs):
            self._flags = 0
        def setWindowTitle(self, t): pass
        def resize(self, w, h): pass
        def setWindowFlags(self, f): self._flags = f
        def windowFlags(self): return self._flags
        def exec_(self): pass
        def accept(self): pass
        def reject(self): pass
        def show(self): pass
    class QGroupBox:
        def __init__(self, *args, **kwargs): pass
        def setLayout(self, l): pass
    class QTextEdit:
        def __init__(self, *args, **kwargs): pass
        def setReadOnly(self, v): pass
        def setHtml(self, h): pass
    class QDialogButtonBox:
        Close = 1
        AcceptRole = 0
        RejectRole = 1
        DestructiveRole = 2
        def __init__(self, *args, **kwargs):
            self.rejected = MagicMock()
            self._buttons = []
        def addButton(self, label, role):
            btn = MagicMock()
            btn.label = label
            btn.role = role
            self._buttons.append(btn)
            return btn

qt_mock = MockQt()
sys.modules['PyQt5'] = MagicMock()
sys.modules['PyQt5.Qt'] = qt_mock

# Define real exception classes for tweak
class FakeWorkerError(Exception):
    def __init__(self, msg, orig_tb=None):
        super().__init__(msg)
        self.orig_tb = orig_tb

class FakeError(Exception):
    pass

tweak.WorkerError = FakeWorkerError
tweak.Error = FakeError

# ---------------------------------------------------------------------------
# Bootstrap the calibre_plugins.language_clean_plugin namespace so that
# relative imports inside the plugin modules resolve to the project directory.
# This avoids needing any on-disk package structure outside the repo.
# ---------------------------------------------------------------------------
_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# Create the calibre_plugins namespace package in sys.modules
_cp_pkg = types.ModuleType('calibre_plugins')
_cp_pkg.__path__ = [_PROJECT_DIR]
_cp_pkg.__package__ = 'calibre_plugins'
sys.modules['calibre_plugins'] = _cp_pkg

# Create the language_clean_plugin sub-package pointing at the project dir
_plugin_pkg = types.ModuleType('calibre_plugins.language_clean_plugin')
_plugin_pkg.__path__ = [_PROJECT_DIR]
_plugin_pkg.__package__ = 'calibre_plugins.language_clean_plugin'
_plugin_pkg.__spec__ = importlib.util.spec_from_file_location(
    'calibre_plugins.language_clean_plugin',
    os.path.join(_PROJECT_DIR, '__init__.py'),
    submodule_search_locations=[_PROJECT_DIR],
)
sys.modules['calibre_plugins.language_clean_plugin'] = _plugin_pkg

# Execute __init__.py into the package NOW so CleanerPlugin is available
# when action.py imports it at module level.
_init_spec = importlib.util.spec_from_file_location(
    'calibre_plugins.language_clean_plugin',
    os.path.join(_PROJECT_DIR, '__init__.py'),
)
_init_spec.loader.exec_module(_plugin_pkg)

def load_plugin_mod(name):
    """Import a plugin submodule, re-loading it fresh each time."""
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
config_widget = load_plugin_mod('config_widget')
plugin = _plugin_pkg

class TestUI(unittest.TestCase):

    def test_config_defaults(self):
        # Per-group profanity flags — all on by default
        self.assertTrue(config_plugin.prefs.defaults['replace_slurs'])
        self.assertTrue(config_plugin.prefs.defaults['replace_crude'])
        self.assertTrue(config_plugin.prefs.defaults['replace_damn'])
        self.assertTrue(config_plugin.prefs.defaults['replace_bitch'])
        self.assertTrue(config_plugin.prefs.defaults['replace_shit'])
        self.assertTrue(config_plugin.prefs.defaults['replace_fbomb'])
        self.assertTrue(config_plugin.prefs.defaults['replace_hell'])
        # Religious
        self.assertTrue(config_plugin.prefs.defaults['replace_religious'])
        self.assertEqual(config_plugin.prefs.defaults['replace_vain_lord'], 'auto')
        self.assertFalse(config_plugin.prefs.defaults['replace_god'])
        # Ass mode
        self.assertEqual(config_plugin.prefs.defaults['ass_mode'], 'auto')
        self.assertTrue(config_plugin.prefs.defaults['replace_ass'])

    def test_config_widget_commit(self):
        # Mock all Qt widgets before __init__ instantiates them
        with patch('calibre_plugins.language_clean_plugin.config_widget.QCheckBox', return_value=MagicMock()), \
             patch('calibre_plugins.language_clean_plugin.config_widget.QComboBox', return_value=MagicMock()), \
             patch('calibre_plugins.language_clean_plugin.config_widget.QTableWidget', return_value=MagicMock()), \
             patch('calibre_plugins.language_clean_plugin.config_widget.QLineEdit', return_value=MagicMock()), \
             patch('calibre_plugins.language_clean_plugin.config_widget.QGroupBox', return_value=MagicMock()):
            widget = config_widget.ConfigWidget()

        # Wire up all the per-group boolean checkboxes
        widget.slurs = MagicMock(); widget.slurs.isChecked.return_value = True
        widget.crude = MagicMock(); widget.crude.isChecked.return_value = True
        widget.damn  = MagicMock(); widget.damn.isChecked.return_value  = False
        widget.bitch = MagicMock(); widget.bitch.isChecked.return_value = True
        widget.shit  = MagicMock(); widget.shit.isChecked.return_value  = True
        widget.fbomb = MagicMock(); widget.fbomb.isChecked.return_value = False
        widget.hell  = MagicMock(); widget.hell.isChecked.return_value  = True
        widget.religious = MagicMock(); widget.religious.isChecked.return_value = True
        widget.replace_god = MagicMock(); widget.replace_god.isChecked.return_value = True
        widget.backup  = MagicMock(); widget.backup.isChecked.return_value  = True
        widget.confirm = MagicMock(); widget.confirm.isChecked.return_value = True
        widget.show_setup = MagicMock(); widget.show_setup.isChecked.return_value = True
        widget.write_log = MagicMock(); widget.write_log.isChecked.return_value = True
        widget.log_dir = MagicMock(); widget.log_dir.text.return_value = ''

        # vain_lord combo: index 1 → 'always'
        widget.vain_lord = MagicMock()
        widget.vain_lord.currentIndex.return_value = 1

        # ass_mode combo: index 2 → 'clean'
        widget.ass_mode = MagicMock()
        widget.ass_mode.currentIndex.return_value = 2
        widget.replace_ass = MagicMock(); widget.replace_ass.isChecked.return_value = False

        # Mock table with one row
        widget.table = MagicMock()
        widget.table.rowCount.return_value = 1
        widget.palette = MagicMock(return_value=MagicMock())
        mock_item = MagicMock()
        mock_item.text.return_value = 'find'
        widget.table.item.side_effect = lambda r, c: mock_item if c < 2 else None

        mock_container = MagicMock()
        mock_checkbox = MagicMock()
        mock_checkbox.isChecked.return_value = True
        mock_container.checkbox = mock_checkbox
        widget.table.cellWidget.return_value = mock_container

        with patch('calibre_plugins.language_clean_plugin.config_widget.prefs') as mock_prefs, \
             patch('calibre.gui2.error_dialog') as mock_err:
            try:
                result = widget.commit()
                print(f"Commit result: {result}")
                if not result:
                    print(f"Error dialog calls: {mock_err.call_args_list}")
            except Exception as e:
                print(f"Commit exception: {e}")
                raise e
            print(f"Set calls: {mock_prefs.set.call_args_list}")

            mock_prefs.set.assert_any_call('replace_slurs',    True)
            mock_prefs.set.assert_any_call('replace_crude',    True)
            mock_prefs.set.assert_any_call('replace_damn',     False)
            mock_prefs.set.assert_any_call('replace_bitch',    True)
            mock_prefs.set.assert_any_call('replace_shit',     True)
            mock_prefs.set.assert_any_call('replace_fbomb',    False)
            mock_prefs.set.assert_any_call('replace_hell',     True)
            mock_prefs.set.assert_any_call('replace_religious', True)
            mock_prefs.set.assert_any_call('replace_god',       True)
            mock_prefs.set.assert_any_call('replace_vain_lord', 'always')
            mock_prefs.set.assert_any_call('replace_ass',       False)
            mock_prefs.set.assert_any_call('ass_mode',          'clean')
            mock_prefs.set.assert_any_call('create_backup',    True)
            mock_prefs.set.assert_any_call('show_confirm_dialog', True)
            mock_prefs.set.assert_any_call('write_log',        True)
            mock_prefs.set.assert_any_call('log_dir',          '')
            mock_prefs.set.assert_any_call('mute_setup_warning', True)
            mock_prefs.set.assert_any_call('custom_replacements', [['find', 'find', True, True]])

    def test_config_widget_mute_setup_warning(self):
        """ConfigWidget should load and save the mute_setup_warning preference directly."""
        with patch('calibre_plugins.language_clean_plugin.config_widget.QCheckBox', side_effect=lambda *a, **k: MagicMock()) as mock_cb_cls, \
             patch('calibre_plugins.language_clean_plugin.config_widget.QComboBox'), \
             patch('calibre_plugins.language_clean_plugin.config_widget.QTableWidget'), \
             patch('calibre_plugins.language_clean_plugin.config_widget.QGroupBox'), \
             patch('calibre_plugins.language_clean_plugin.config_widget.prefs') as mock_prefs:

            # 1. Test loading: warning is NOT muted -> checkbox is UNCHECKED
            mock_prefs.get.side_effect = lambda k, d=None: False if k == 'mute_setup_warning' else d
            widget = config_widget.ConfigWidget()
            widget.show_setup.setChecked.assert_called_with(False)

            # 2. Test loading: warning IS muted -> checkbox is CHECKED
            mock_prefs.get.side_effect = lambda k, d=None: True if k == 'mute_setup_warning' else d
            widget = config_widget.ConfigWidget()
            widget.show_setup.setChecked.assert_called_with(True)

            # 3. Test saving (commit)
            widget.table.rowCount.return_value = 0
            widget.show_setup.isChecked.return_value = True
            widget.commit()
            # If "Mute" is checked, mute_setup_warning should be True
            mock_prefs.set.assert_any_call('mute_setup_warning', True)

            widget.show_setup.isChecked.return_value = False
            widget.commit()
            # If "Mute" is unchecked, mute_setup_warning should be False
            mock_prefs.set.assert_any_call('mute_setup_warning', False)

    def test_config_widget_table_ops(self):
        with patch('calibre_plugins.language_clean_plugin.config_widget.QCheckBox'), \
             patch('calibre_plugins.language_clean_plugin.config_widget.QComboBox'), \
             patch('calibre_plugins.language_clean_plugin.config_widget.QTableWidget'), \
             patch('calibre_plugins.language_clean_plugin.config_widget.QGroupBox'):
            widget = config_widget.ConfigWidget()

        widget.table = MagicMock()
        widget.table.rowCount.return_value = 0

        # Test add row
        widget._add_table_row(['a', 'b', True])
        widget.table.insertRow.assert_called()

        # Test remove row
        widget.table.currentRow.return_value = 0
        widget._remove_table_row()
        widget.table.removeRow.assert_called_with(0)

    @patch('calibre_plugins.language_clean_plugin.action.info_dialog')
    @patch('calibre_plugins.language_clean_plugin.action.error_dialog')
    @patch('calibre_plugins.language_clean_plugin.action.question_dialog')
    @patch('calibre_plugins.language_clean_plugin.config.prefs')
    def test_action_clean_selected_books(self, mock_prefs, mock_question, mock_error, mock_info):
        gui = MagicMock()

        # Patch load_resources on the instance after creation
        act = action.CleanerAction(gui, 'test')
        act.load_resources = MagicMock(return_value={})

        # 1. No books selected
        gui.library_view.selectionModel().selectedRows.return_value = []
        act.clean_selected_books()
        mock_error.assert_called_with(gui, 'No books selected', unittest.mock.ANY, show=True)

        # 2. Books selected, confirm False
        gui.library_view.selectionModel().selectedRows.return_value = [1]
        gui.library_view.get_selected_ids.return_value = [123]
        mock_prefs.get.return_value = True
        mock_question.return_value = False
        db = gui.current_db.new_api
        db.formats.return_value = ['EPUB']   # needed for confirmation detail loop
        act.clean_selected_books()

        # 3. Successful path (mocking db)
        mock_question.return_value = True

        with patch('calibre_plugins.language_clean_plugin.action.tempfile.mkstemp') as mock_mkstemp, \
             patch('calibre_plugins.language_clean_plugin.action.os.close'):
            mock_mkstemp.return_value = (99, 'tmp.epub')
            act.clean_selected_books()

            # Verify job was queued
            gui.job_manager.run_threaded_job.assert_called()

    @patch('calibre_plugins.language_clean_plugin.action.info_dialog')
    @patch('calibre_plugins.language_clean_plugin.action.error_dialog')
    def test_action_preview(self, mock_error, mock_info):
        gui = MagicMock()
        act = action.CleanerAction(gui, 'test')

        # No books selected
        gui.library_view.get_selected_ids.return_value = []
        act.preview_selected_books()
        mock_error.assert_called()

        # Book selected, no formats
        gui.library_view.get_selected_ids.return_value = [123]
        db = gui.current_db.new_api
        db.formats.return_value = []
        act.preview_selected_books()
        mock_error.assert_called()

        # Success path
        db.formats.return_value = ['EPUB']
        with patch('calibre_plugins.language_clean_plugin.action.tempfile.mkstemp') as mock_mkstemp, \
             patch('calibre_plugins.language_clean_plugin.action.os.close'):
            mock_mkstemp.return_value = (99, 'tmp.epub')
            act.preview_selected_books()
            gui.job_manager.run_threaded_job.assert_called()

    def test_action_genesis(self):
        gui = MagicMock()
        act = action.CleanerAction(gui, 'test')
        act.load_resources = MagicMock(return_value={'images/clean.png': b'fake_data'})
        act.qaction = MagicMock()
        act.qaction.menu.return_value = None

        act.genesis()
        act.qaction.setIcon.assert_called()
        act.qaction.setMenu.assert_called()

    def test_library_view_context_menu_actions(self):
        gui = MagicMock()
        act = action.CleanerAction(gui, 'test')
        act.qaction = MagicMock()

        # This is what Calibre expects
        res = act.library_view_context_menu_actions(None, MagicMock())
        self.assertEqual(res, [act.qaction])

    @patch('calibre_plugins.language_clean_plugin.action.gprefs')
    @patch('calibre_plugins.language_clean_plugin.config.prefs')
    def test_initialization_complete(self, mock_prefs, mock_gprefs):
        """
        Tests initialization_complete() — fingerprint reset and QTimer deferral.
        _deferred_setup_check is patched out; its logic is tested separately.
        """
        import unittest.mock as _mock
        import hashlib

        FIXED_MTIME = 1234567890.0
        STABLE_FP = str(FIXED_MTIME)

        patcher_mtime = _mock.patch(
            'calibre_plugins.language_clean_plugin.action.os.path.getmtime',
            return_value=FIXED_MTIME)
        patcher_cfgdir = _mock.patch(
            'calibre_plugins.language_clean_plugin.action.config_dir',
            '/tmp/fake_calibre')
        patcher_mtime.start()
        patcher_cfgdir.start()
        self.addCleanup(patcher_mtime.stop)
        self.addCleanup(patcher_cfgdir.stop)

        gui = MagicMock()
        act = action.CleanerAction(gui, 'test')
        act._deferred_setup_check = MagicMock()

        def _make_prefs_get(mute=False, fp_match=True):
            stored = STABLE_FP if fp_match else None
            def _get(key, default=None):
                if key == 'mute_setup_warning': return mute
                if key == 'plugin_fingerprint': return stored
                return default
            return _get

        with _mock.patch('calibre_plugins.language_clean_plugin.action.QTimer') as MockTimer:
            # 1. Not muted, fp matches — timer queued
            mock_prefs.get.side_effect = _make_prefs_get(mute=False)
            act.initialization_complete()
            MockTimer.singleShot.assert_called_once_with(0, act._deferred_setup_check)

            # 2. Muted — timer NOT queued
            MockTimer.reset_mock()
            mock_prefs.get.side_effect = _make_prefs_get(mute=True)
            act.initialization_complete()
            MockTimer.singleShot.assert_not_called()

            # 3. Fingerprint mismatch (reinstall) — mute reset, timer queued
            MockTimer.reset_mock()
            mock_prefs.reset_mock()
            state = {'mute': True, 'fp': None}

            def _sg(key, default=None):
                if key == 'mute_setup_warning': return state['mute']
                if key == 'plugin_fingerprint': return state['fp']
                return default

            def _ss(key, value):
                if key == 'mute_setup_warning': state['mute'] = value
                if key == 'plugin_fingerprint': state['fp'] = value

            mock_prefs.get.side_effect = _sg
            mock_prefs.set.side_effect = _ss
            act.initialization_complete()
            mock_prefs.set.side_effect = None

            reset_calls = [c for c in mock_prefs.set.call_args_list
                           if c.args[0] == 'mute_setup_warning']
            self.assertTrue(reset_calls)
            self.assertFalse(reset_calls[0].args[1])
            MockTimer.singleShot.assert_called_once()

    def test_deferred_setup_check(self):
        """Tests _deferred_setup_check routing — which args show_setup_notice gets."""
        gui = MagicMock()
        act = action.CleanerAction(gui, 'test')
        act.show_setup_notice = MagicMock()
        act.qaction = MagicMock()

        # Helper: configure gui mocks so is_on_any_toolbar / is_in_context_menu
        # return the desired values.  We patch the methods directly since the
        # underlying gui.bars_manager structure is complex to mock faithfully.
        def _set_location(toolbar=False, context=False):
            act.is_on_any_toolbar = MagicMock(return_value=toolbar)
            act.is_in_context_menu = MagicMock(return_value=context)

        # Both present — no notice
        _set_location(toolbar=True, context=True)
        act._deferred_setup_check()
        act.show_setup_notice.assert_not_called()

        # Both missing
        _set_location(toolbar=False, context=False)
        act._deferred_setup_check()
        act.show_setup_notice.assert_called_once_with(True, True)

        # Only toolbar missing
        act.show_setup_notice.reset_mock()
        _set_location(toolbar=False, context=True)
        act._deferred_setup_check()
        act.show_setup_notice.assert_called_once_with(True, False)

        # Only context missing
        act.show_setup_notice.reset_mock()
        _set_location(toolbar=True, context=False)
        act._deferred_setup_check()
        act.show_setup_notice.assert_called_once_with(False, True)
    @patch('calibre_plugins.language_clean_plugin.config.prefs')
    def test_show_setup_notice_choices(self, mock_prefs):
        """Tests all three button paths of the 3-button notice dialog."""
        import unittest.mock as _mock
        import sys

        gui = MagicMock()
        act = action.CleanerAction(gui, 'test')
        act.show_setup_instructions = MagicMock()

        def _run_notice_with_button(button_key):
            """Run show_setup_notice, firing the named button during exec_."""
            callbacks = {}

            with _mock.patch('calibre_plugins.language_clean_plugin.action.QDialog') as MockDlg, \
                 _mock.patch('calibre_plugins.language_clean_plugin.action.QDialogButtonBox') as MockBtnBox, \
                 _mock.patch('calibre_plugins.language_clean_plugin.action.QVBoxLayout'), \
                 _mock.patch('calibre_plugins.language_clean_plugin.action.QLabel'):

                dlg = MagicMock()
                dlg.windowFlags.return_value = 0
                MockDlg.return_value = dlg

                btn_box = MagicMock()
                MockBtnBox.return_value = btn_box
                show_btn = MagicMock()
                later_btn = MagicMock()
                never_btn = MagicMock()
                btn_box.addButton.side_effect = [show_btn, later_btn, never_btn]

                show_btn.clicked.connect.side_effect  = lambda fn: callbacks.__setitem__('show', fn)
                later_btn.clicked.connect.side_effect = lambda fn: callbacks.__setitem__('later', fn)
                never_btn.clicked.connect.side_effect = lambda fn: callbacks.__setitem__('never', fn)

                dlg.exec_.side_effect = lambda: callbacks[button_key]()

                act.show_setup_instructions.reset_mock()
                mock_prefs.set.reset_mock()
                act.show_setup_notice(True, True)

        # "Show me how" → instructions shown, nothing muted
        _run_notice_with_button('show')
        act.show_setup_instructions.assert_called_once_with(True, True)
        mock_prefs.set.assert_not_called()

        # "Remind me later" → nothing shown, nothing muted
        _run_notice_with_button('later')
        act.show_setup_instructions.assert_not_called()
        mock_prefs.set.assert_not_called()

        # "Don't remind me" → nothing shown, muted
        _run_notice_with_button('never')
        act.show_setup_instructions.assert_not_called()
        mock_prefs.set.assert_called_once_with('mute_setup_warning', True)
    @patch('calibre_plugins.language_clean_plugin.action.error_dialog')
    @patch('calibre_plugins.language_clean_plugin.action.info_dialog')
    def test_on_clean_complete_shows_error_dialog_on_item_error(self, mock_info, mock_error):
        """
        When a work item has an error (e.g. MOBI KF8 unpack failure),
        _on_clean_complete must call error_dialog, not info_dialog.
        """
        gui = MagicMock()
        act = action.CleanerAction(gui, 'test')

        # Simulate a job that completed but one item has an error
        job = MagicMock()
        job.failed = False
        job.result = [
            {
                'book_id': 1,
                'title': 'Test Book',
                'fmt': 'mobi',
                'path': None,
                'changes_made': False,
                'count': 0,
                'error': ('This MOBI file does not contain a KF8 format book. '
                          'KF8 is the new format from Amazon.'),
            }
        ]

        act._on_clean_complete(job)

        # Must use error_dialog, not info_dialog
        mock_error.assert_called_once()
        mock_info.assert_not_called()

        # KF8 tip must appear in the detail text
        det_msg = mock_error.call_args.kwargs.get('det_msg', '')
        self.assertIn('KF8', det_msg)
        self.assertIn('MOBI file type', det_msg)

    @patch('calibre_plugins.language_clean_plugin.action.info_dialog')
    def test_on_clean_complete_info_when_no_errors(self, mock_info):
        """When there are no errors, _on_clean_complete uses info_dialog."""
        gui = MagicMock()
        act = action.CleanerAction(gui, 'test')

        job = MagicMock()
        job.failed = False
        job.result = [
            {
                'book_id': 1,
                'title': 'Test Book',
                'fmt': 'epub',
                'path': None,
                'changes_made': False,
                'count': 0,
                'error': None,
            }
        ]

        act._on_clean_complete(job)
        mock_info.assert_called_once()

    @patch('calibre_plugins.language_clean_plugin.config.prefs')
    @patch('calibre_plugins.language_clean_plugin.action.info_dialog')
    def test_on_clean_complete_refreshes_book_details(self, mock_info, mock_prefs):
        """
        After cleaning, _on_clean_complete must call model().current_changed(idx, idx)
        so the Book Details panel re-queries the db and shows ORIGINAL_EPUB immediately
        without the user having to click away and back.

        gui.book_details is a QSplitter in Calibre 9+ and has no refresh(book_id)
        method, so we must NOT call it directly.
        """
        import os, tempfile

        mock_prefs.get.return_value = False   # create_backup=False, keep it simple

        gui = MagicMock()

        # currentIndex() must return a valid index so the guard passes
        valid_idx = MagicMock()
        valid_idx.isValid.return_value = True
        gui.library_view.currentIndex.return_value = valid_idx

        act = action.CleanerAction(gui, 'test')

        fd, tmp = tempfile.mkstemp(suffix='.epub')
        os.close(fd)
        try:
            job = MagicMock()
            job.failed = False
            job.result = [
                {
                    'book_id': 42,
                    'title': 'Test Book',
                    'fmt': 'epub',
                    'path': tmp,
                    'changes_made': True,
                    'count': 3,
                    'error': None,
                }
            ]

            act._on_clean_complete(job)

            # model().current_changed must be called with (idx, idx)
            gui.library_view.model().current_changed.assert_called_once_with(
                valid_idx, valid_idx)

            # book_details.refresh(book_id) must NOT be called — it doesn't
            # exist on QSplitter (Calibre 9+) and would raise TypeError.
            gui.book_details.refresh.assert_not_called()

        finally:
            if os.path.exists(tmp):
                os.remove(tmp)



    def test_language_check_per_group_flags(self):
        """Disabling individual word-family flags removes only that group's rules."""
        c = sys.modules['calibre_plugins.language_clean_plugin.cleaner']
        language_check = c.language_check
        slur_list = c.slur_list; crude_list = c.crude_list
        damn_list = c.damn_list; bitch_list = c.bitch_list
        shit_list = c.shit_list; fbomb_list = c.fbomb_list
        hell_list = c.hell_list; lord_list  = c.lord_list
        vain_lord_list = c.vain_lord_list; clean_a_list = c.clean_a_list

        # All on (default) — every sub-list present
        rules = language_check('normal text')
        for group in (slur_list, crude_list, damn_list, bitch_list,
                      shit_list, fbomb_list, hell_list, lord_list):
            self.assertTrue(
                any(r in rules for r in group),
                'Expected group to be included by default: %r' % (group[0],)
            )

        # Disable slurs only
        rules = language_check('normal text', replace_slurs=False)
        for r in slur_list:
            self.assertNotIn(r, rules)
        self.assertTrue(any(r in rules for r in damn_list))

        # Disable damn only
        rules = language_check('normal text', replace_damn=False)
        for r in damn_list:
            self.assertNotIn(r, rules)
        self.assertTrue(any(r in rules for r in shit_list))

        # Disable bitch only
        rules = language_check('normal text', replace_bitch=False)
        for r in bitch_list:
            self.assertNotIn(r, rules)

        # Disable shit only
        rules = language_check('normal text', replace_shit=False)
        for r in shit_list:
            self.assertNotIn(r, rules)

        # Disable fbomb only
        rules = language_check('normal text', replace_fbomb=False)
        for r in fbomb_list:
            self.assertNotIn(r, rules)

        # Disable hell only
        rules = language_check('normal text', replace_hell=False)
        for r in hell_list:
            self.assertNotIn(r, rules)

        # Disable ass only — compounds AND standalone lists gone
        rules_no_ass = language_check('normal text', replace_ass=False)
        for r in c.ass_compound_list + c.dirty_a_list + c.clean_a_list:
            self.assertNotIn(r, rules_no_ass)
        self.assertTrue(any(r in rules_no_ass for r in damn_list))

        # Disable crude only (non-ass portion)
        rules = language_check('normal text', replace_crude=False)
        for r in c.crude_non_ass_list:
            self.assertNotIn(r, rules)

        # Disable religious — neither lord_list nor vain_lord_list present
        rules = language_check('for Christ\'s sake!', replace_religious=False)
        for r in lord_list:
            self.assertNotIn(r, rules)
        for r in vain_lord_list:
            self.assertNotIn(r, rules)

        # All off — result should be empty (no ass list either)
        rules = language_check(
            'normal text',
            replace_slurs=False, replace_crude=False, replace_damn=False,
            replace_bitch=False, replace_shit=False, replace_fbomb=False,
            replace_hell=False, replace_religious=False, replace_ass=False,
        )
        self.assertEqual(rules, [])
        for group in (slur_list, c.crude_non_ass_list, c.ass_compound_list,
                      damn_list, bitch_list, shit_list, fbomb_list, hell_list,
                      lord_list, vain_lord_list, c.dirty_a_list, c.clean_a_list):
            for r in group:
                self.assertNotIn(r, rules)

    def test_re_list_equals_sub_list_concatenation(self):
        """re_list must equal the concatenation of all categorised sub-lists."""
        c = sys.modules['calibre_plugins.language_clean_plugin.cleaner']
        re_list = c.re_list
        combined = (c.slur_list + c.crude_list + c.damn_list + c.bitch_list
                    + c.shit_list + c.fbomb_list + c.hell_list)
        self.assertEqual(re_list, combined,
                         're_list must equal slur+crude+damn+bitch+shit+fbomb+hell (same order)')

    def test_replace_god_flag(self):
        """replace_god=True replaces every standalone God; False leaves it alone."""
        c = sys.modules['calibre_plugins.language_clean_plugin.cleaner']
        engine_on  = c.RuleEngine(c.language_check('', replace_god=True,  replace_religious=False))
        engine_off = c.RuleEngine(c.language_check('', replace_god=False, replace_religious=False))

        cases = [
            ('God',          'Goodness'),      # capital G → capital G via keep_case
            ('GOD',          'GOODNESS'),
            ('Oh God help',  'Oh Goodness help'),
            ('of God',       'of Goodness'),   # no exceptions — all replaced
            ('God bless',    'Goodness bless'),
            ('God save',     'Goodness save'),
            ('Godspeed',     'Godspeed'),       # not a word boundary match
        ]
        for text, expected in cases:
            self.assertEqual(engine_on.process_line(text), expected,
                             'replace_god=True: %r' % text)
            # With flag off, text should be unchanged (no religious rules at all)
            self.assertEqual(engine_off.process_line(text), text,
                             'replace_god=False: %r should be unchanged' % text)

    def test_god_replace_list_not_in_re_list(self):
        """god_replace_list must not appear in re_list (it's opt-in only)."""
        c = sys.modules['calibre_plugins.language_clean_plugin.cleaner']
        for r in c.god_replace_list:
            self.assertNotIn(r, c.re_list)
            self.assertNotIn(r, c.lord_list)
            self.assertNotIn(r, c.vain_lord_list)
        """_vain_stored_value() maps combo indices to internal strings."""
        with patch('calibre_plugins.language_clean_plugin.config_widget.QCheckBox'), \
             patch('calibre_plugins.language_clean_plugin.config_widget.QComboBox'), \
             patch('calibre_plugins.language_clean_plugin.config_widget.QTableWidget'), \
             patch('calibre_plugins.language_clean_plugin.config_widget.QGroupBox'):
            widget = config_widget.ConfigWidget()

        widget.vain_lord = MagicMock()
        for idx, expected in [(0, 'auto'), (1, 'always'), (2, 'never')]:
            widget.vain_lord.currentIndex.return_value = idx
            self.assertEqual(widget._vain_stored_value(), expected,
                             'index %d should map to %r' % (idx, expected))

    def test_config_widget_ass_combo_stored_values(self):
        """_ass_stored_value() maps combo indices to internal strings."""
        with patch('calibre_plugins.language_clean_plugin.config_widget.QCheckBox'), \
             patch('calibre_plugins.language_clean_plugin.config_widget.QComboBox'), \
             patch('calibre_plugins.language_clean_plugin.config_widget.QTableWidget'), \
             patch('calibre_plugins.language_clean_plugin.config_widget.QGroupBox'):
            widget = config_widget.ConfigWidget()

        widget.ass_mode = MagicMock()
        for idx, expected in [(0, 'auto'), (1, 'dirty'), (2, 'clean')]:
            widget.ass_mode.currentIndex.return_value = idx
            self.assertEqual(widget._ass_stored_value(), expected,
                             'index %d should map to %r' % (idx, expected))

    def test_prefs_snapshot_contains_new_keys(self):
        """_snapshot_prefs() must include all new per-group keys."""
        gui = MagicMock()
        act = action.CleanerAction(gui, 'test')
        mock_defaults = {
            'replace_slurs': True, 'replace_crude': True,
            'replace_damn': True,  'replace_bitch': True,
            'replace_shit': True,  'replace_fbomb': True,
            'replace_hell': True,  'replace_religious': True,
            'replace_vain_lord': 'auto', 'ass_mode': 'auto',
            'replace_ass': True,   'replace_god': False,
            'custom_replacements': [], 'create_backup': True,
            'show_confirm_dialog': True, 'write_log': False,
            'log_dir': '', 'mute_setup_warning': False,
            'plugin_fingerprint': None,
        }
        with patch('calibre_plugins.language_clean_plugin.config.prefs') as mock_prefs:
            mock_prefs.defaults = mock_defaults
            mock_prefs.get.side_effect = lambda k, d=None: mock_defaults.get(k, d)
            snap = act._snapshot_prefs()

        expected_keys = [
            'replace_slurs', 'replace_crude', 'replace_damn', 'replace_bitch',
            'replace_shit', 'replace_fbomb', 'replace_hell', 'replace_religious',
            'replace_vain_lord', 'ass_mode', 'replace_ass', 'replace_god',
            'mute_setup_warning',
        ]
        for key in expected_keys:
            self.assertIn(key, snap, 'Snapshot missing key: %s' % key)


if __name__ == '__main__':
    unittest.main()
