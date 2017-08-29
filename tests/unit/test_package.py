from unittest import TestCase

import omnium


class TestPackage(TestCase):
    def test_load(self):
        assert hasattr(omnium, 'Stash')
        assert hasattr(omnium, 'omnium_main')

    def test_init(self):
        stash = omnium.init()

    def test_setup_ipython(self):
        # Check it won't load if it thinks it's not interactive.
        with self.assertRaises(Exception):
            omnium.setup_ipython()
        # Make it think it's interactive.
        import __main__ as main
        delattr(main, '__file__')
        omnium.setup_ipython()
