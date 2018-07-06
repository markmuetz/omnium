import os
import subprocess as sp
from logging import getLogger

import iris
import numpy as np
from omnium.omnium_errors import OmniumError

logger = getLogger('om.utils')


def get_git_info(location):
    cwd = os.getcwd()
    os.chdir(location)
    try:
        git_hash = sp.check_output('git rev-parse HEAD'.split()).strip()
        if sp.check_output('git status --porcelain'.split()) == b'':
            return git_hash, 'clean'
        else:
            return git_hash, 'uncommitted_changes'
    except sp.CalledProcessError as ex:
        return None, 'not_git_repo'
    finally:
        os.chdir(cwd)


def is_power_of_two(num):
    return num & (num - 1) == 0


def coarse_grain(data, mask, npow=None):
    assert data.ndim == 2
    assert data.shape[0] == data.shape[1]
    assert is_power_of_two(data.shape[0])

    nx = data.shape[0]
    if not npow:
        npow = int(np.log2(data.shape[0]))

    coarse_data = []
    # Don't go to the grid scale (i.e. don't use npow + 1).
    for n in 2**np.arange(npow):
        coarse = np.zeros((n, n))
        l = nx / n
        for i in range(n):
            s1 = slice(i * l, (i + 1) * l)
            for j in range(n):
                s2 = slice(j * l, (j + 1) * l)
                coarse[i, j] = data[s1, s2][mask[s1, s2]].sum()
        coarse_data.append((n, coarse))
    return coarse_data


def get_cube_from_attr(cubes, key, value):
    for cube in cubes:
        if key in cube.attributes:
            if cube.attributes[key] == value:
                return cube
    raise OmniumError('Cube with ({}, {}) not found'.format(key, value))


def get_cube(cubes, section, item):
    for cube in cubes:
        stash = cube.attributes['STASH']
        if stash.section == section and stash.item == item:
            return cube
    raise OmniumError('Cube ({}, {}) not found'.format(section, item))


def get_cubes(cubes, section, item):
    ret_cubes = []
    for cube in cubes:
        stash = cube.attributes['STASH']
        if stash.section == section and stash.item == item:
            ret_cubes.append(cube)
    if ret_cubes:
        return iris.cube.CubeList(ret_cubes)
    else:
        raise OmniumError('No cubes found ({}, {})'.format(section, item))


class cd:
    def __init__(self, dir):
        self.dir = dir

    def __enter__(self):
        self.cwd = os.getcwd()
        logger.debug('cd to {}', self.dir)
        os.chdir(self.dir)

    def __exit__(self, type, value, traceback):
        logger.debug('cd to {}', self.cwd)
        os.chdir(self.cwd)
