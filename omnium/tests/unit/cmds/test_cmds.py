# I know it's deprecated, but I don't know how to use importlib to achieve same result.
import imp
import os
from unittest import TestCase

import omnium
from mock import patch
from omnium.converter import FF2NC_Converter
from omnium.omnium_cmd import main as omnium_main
from omnium.version import get_version
from omnium.cmds import modules
try:
    from omnium.viewers.viewer_control import ViewerControlWindow
    from pyqtgraph.Qt import QtGui
    test_viewer = True
except ImportError:
    test_viewer = False


def test_src_generator():
    for command_module in modules.values():
        yield _test_module_docstring, command_module


def _test_module_docstring(command_module):
    print(command_module)
    assert command_module.__doc__, 'Docstring for {} empty'.format(command_module)


class TestCmds(TestCase):
    """Only test commands that can be run outside of an omnium suite."""
    @patch.object(FF2NC_Converter, 'analysis_done')
    @patch.object(FF2NC_Converter, 'save')
    def test_convert(self, mock_save, mock_done):
        omnium_main(['omnium', 'convert', 'filename'])
        mock_save.assert_called()
        mock_done.assert_called()

    @patch('IPython.embed')
    def test_shell(self, mock_embed):
        omnium_main(['omnium', 'shell'])
        mock_embed.assert_called()

        mock_embed.reset_mock()
        omnium_main(['omnium', 'shell', '--failsafe'])

    def test_stash(self):
        omnium_main(['omnium', 'stash'])
        omnium_main(['omnium', 'stash', '--search', 'density'])
        omnium_main(['omnium', 'stash', '--get-name', '0,150'])

    def test_stash_fail(self):
        with self.assertRaises(omnium.OmniumError):
            omnium_main(['omnium', 'stash', '--get-name', '0:150'])  # Should be a comma.

    def test_version(self):
        omnium_main(['omnium', 'version'])

    def test_version_long(self):
        omnium_main(['omnium', 'version', '--long'])

    def test_version_bad_arg(self):
        with self.assertRaises(ValueError):
            get_version(form='arg_not_handled')

    def test_version_run_cmd(self):
        # Quite hard to test if __name__ == '__main__': with source coverage. Use this trick:
        # https://stackoverflow.com/a/5850288/54557
        imp.load_source('__main__', os.path.join(os.path.dirname(omnium.__file__), 'version.py'))

    if test_viewer:
        @patch.object(QtGui.QApplication, 'exec_')
        @patch.object(ViewerControlWindow, 'show')
        def test_viewer_control(self, mock_show, mock_exec):
            omnium_main(['omnium', 'viewer'])
            mock_show.assert_called()
            mock_exec.assert_called()
