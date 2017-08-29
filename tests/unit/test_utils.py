from unittest import TestCase

from mock import Mock
import numpy as np

import omnium


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


class TestCountBlobMask(TestCase):
    @classmethod
    def setUpClass(cls):
        base_array = np.arange(121).reshape(11, 11)
        cls.checkerboard = base_array % 2 == 0

        cls.wrap = np.zeros((11, 11))
        cls.wrap[0, 5] = 1
        cls.wrap[10, 5] = 1

        cls.spiral = np.zeros((11, 11))
        pos = [5, 5]
        dxdys = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        cls.spiral[pos[0], pos[1]] = 1
        try:
            for i in range(8):
                dxdy = dxdys[i % 4]
                for j in range(i):
                    pos[0] += dxdy[0]
                    pos[1] += dxdy[1]
                    cls.spiral[pos[0], pos[1]] = 1
        except IndexError:
            pass

    def test_checkerboard(self):
        max_index, blobs = omnium.utils.count_blobs_mask(TestCountBlobMask.checkerboard, wrap=False)
        assert max_index == 61
        max_index, blobs = omnium.utils.count_blobs_mask(TestCountBlobMask.checkerboard, diagonal=True)
        assert max_index == 1

    def test_wrap(self):
        max_index, blobs = omnium.utils.count_blobs_mask(TestCountBlobMask.wrap, wrap=False)
        assert max_index == 2
        max_index, blobs = omnium.utils.count_blobs_mask(TestCountBlobMask.wrap, wrap=True)
        assert max_index == 1

    def test_spiral(self):
        max_index, blobs = omnium.utils.count_blobs_mask(TestCountBlobMask.spiral)
        assert max_index == 1
        max_index, blobs = omnium.utils.count_blobs_mask(TestCountBlobMask.spiral, diagonal=True)
        assert max_index == 1
        max_index, blobs = omnium.utils.count_blobs_mask(TestCountBlobMask.spiral, wrap=True)
        assert max_index == 1
