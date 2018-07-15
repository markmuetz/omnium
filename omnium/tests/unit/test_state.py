from unittest import TestCase

import omnium
from omnium.pkg_state import PkgState


class TestState(TestCase):
    def test(self):
        state = PkgState(omnium)
        print(state)
