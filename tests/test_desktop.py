import unittest
from unittest.mock import patch
from inflation_digitizer.desktop import configure_desktop_backend


class DesktopTests(unittest.TestCase):
    def test_mac_cli_explicitly_selects_native_window(self):
        with patch('inflation_digitizer.desktop.sys.platform', 'darwin'), \
             patch('matplotlib.use') as use, \
             patch('importlib.import_module') as load:
            configure_desktop_backend()
        use.assert_called_once_with('MacOSX', force=True)
        load.assert_called_once_with('matplotlib.backends.backend_macosx')

    def test_missing_gui_backend_reports_actionable_error(self):
        with patch('matplotlib.use', side_effect=ImportError('missing GUI')):
            with self.assertRaisesRegex(RuntimeError, 'desktop Python interpreter'):
                configure_desktop_backend()
