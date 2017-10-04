import os
import imp
from unittest import TestCase

from mock import patch
from pyqtgraph.Qt import QtGui

from omnium.omnium_cmd import main as omnium_main
from omnium.version import get_version
import omnium
from omnium.converter import Converter
from omnium.viewers.viewer_control import ViewerControlWindow


class TestCmds(TestCase):
    """Only test commands that can be run outside of an omnium suite."""
    @patch.object(Converter, 'convert')
    def test_convert(self, mock_convert):
        omnium_main(['omnium', 'convert', 'filename'])
        mock_convert.assert_called_with('filename')

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
            get_version('arg_not_handled')

    def test_version_run_cmd(self):
        # Quite hard to test if __name__ == '__main__': with source coverage. Use this trick:
        # https://stackoverflow.com/a/5850288/54557
        imp.load_source('__main__', os.path.join(os.path.dirname(omnium.__file__), 'version.py'))

    @patch.object(QtGui.QApplication, 'exec_')
    @patch.object(ViewerControlWindow, 'show')
    def test_viewer_control(self, mock_show, mock_exec):
        omnium_main(['omnium', 'viewer'])
        mock_show.assert_called()
        mock_exec.assert_called()
