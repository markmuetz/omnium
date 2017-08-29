from unittest import TestCase

from omnium.state import State


class TestState(TestCase):
    def test(self):
        state = State()
        print(state)
