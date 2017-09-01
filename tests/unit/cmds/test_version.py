import os
import imp
from unittest import TestCase

from omnium.omnium_cmd import main as omnium_main
from omnium.version import get_version
import omnium


class TestVersion(TestCase):
    def test_version(self):
        omnium_main(['omnium', 'version'])

    def test_version_long(self):
        omnium_main(['omnium', 'version', '--long'])

    def test_version_bad_arg(self):
        with self.assertRaises(ValueError):
            get_version('arg_not_handled')

    def test_run_version(self):
        # Quite hard to test if __name__ == '__main__':. Use this trick:
        # https://stackoverflow.com/a/5850288/54557
        imp.load_source('__main__', os.path.join(os.path.dirname(omnium.__file__), 'version.py'))
