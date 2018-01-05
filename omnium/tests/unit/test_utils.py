from unittest import TestCase

import omnium
import omnium.consts as consts
from mock import Mock


class TestUtilsGetCube(TestCase):
    @classmethod
    def setUpClass(cls):
        cubes = []
        for i in range(1, 11):
            stash = Mock()
            stash.section = 0
            stash.item = i
            cube = Mock()
            cube.attributes = {'STASH': stash, 'cust_attr': str(i + 1)}
            cubes.append(cube)
        cls.cubes = cubes

    def test_consts(self):
        assert hasattr(consts, 'g')
        assert hasattr(consts, 'L')
        assert hasattr(consts, 'cp')
        assert hasattr(consts, 'Re')

    def test_get_cube(self):
        omnium.utils.get_cube(TestUtilsGetCube.cubes, 0, 10)

    def test_get_cube_fail(self):
        with self.assertRaises(omnium.OmniumError):
            omnium.utils.get_cube(TestUtilsGetCube.cubes, 1, 10)

    def test_get_cubes(self):
        cubes = omnium.utils.get_cubes(TestUtilsGetCube.cubes, 0, 10)
        assert len(cubes) == 1

    def test_get_cubes_fail(self):
        with self.assertRaises(omnium.OmniumError):
            omnium.utils.get_cubes(TestUtilsGetCube.cubes, 0, 22)

    def test_get_cube_from_attr(self):
        omnium.utils.get_cube_from_attr(TestUtilsGetCube.cubes, 'cust_attr', '8')

    def test_get_cube_from_attr_fail(self):
        with self.assertRaises(omnium.OmniumError):
            omnium.utils.get_cube_from_attr(TestUtilsGetCube.cubes, 'cust_attr', 'not_there')
