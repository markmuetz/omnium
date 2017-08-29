from unittest import TestCase

from omnium.omnium_cmd import main as omnium_main


class TestVersion(TestCase):
    def test_version(self):
        omnium_main(['omnium', 'version'])

    def test_version_long(self):
        omnium_main(['omnium', 'version', '--long'])
