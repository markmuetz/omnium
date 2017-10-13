from unittest import TestCase

from omnium.stash import Stash


class TestStash(TestCase):
    def test_load(self):
        stash = Stash()

    def test_search(self):
        stash = Stash()
        res = stash.search('Density')

    def test_get_name(self):
        stash = Stash()
        res = stash.get_name(0, 205)
