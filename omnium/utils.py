import os
import subprocess as sp

import numpy as np

from omnium.omnium_errors import OmniumError


def get_git_info(location):
    cwd = os.getcwd()
    os.chdir(location)
    try:
        git_hash = sp.check_output('git rev-parse HEAD'.split()).strip()
        if sp.check_output('git status --porcelain'.split()) == '':
            return git_hash, 'clean'
        else:
            return git_hash, 'uncommitted_changes'
    except sp.CalledProcessError as ex:
        return None, 'not_git_repo'
    finally:
        os.chdir(cwd)


def is_power_of_two(num):
    return num & (num - 1) == 0


def coarse_grain(data, mask):
    assert data.ndim == 2
    assert data.shape[0] == data.shape[1]
    assert is_power_of_two(data.shape[0])

    nx = data.shape[0]
    pow = int(np.log2(data.shape[0]))

    coarse_data = []
    for n in 2**np.arange(pow + 1):
        coarse = np.zeros((n, n))
        l = nx / n
        for i in range(n):
            s1 = slice(i * l, (i + 1) * l)
            for j in range(n):
                s2 = slice(j * l, (j + 1) * l)
                coarse[i, j] = data[s1, s2][mask[s1, s2]].sum()
        coarse_data.append((n, coarse))
    return coarse_data


def test_indices(i, j, diagonal=False, extended=False):
    if extended:
        # Count any cells in a 5x5 area centred on the current i, j cell as being adjacent.
        indices = []
        for ii in range(i - 2, i + 3):
            for jj in range(j - 2, j + 3):
                indices.append((ii, jj))
    else:
        # Standard, cells sharing a border are adjacent.
        indices = [(i-1, j), (i+1, j), (i, j-1), (i, j+1)]
        if diagonal:
            # Diagonal cells considered adjacent.
            indices += [(i-1, j-1), (i-1, j+1), (i+1, j-1), (i+1, j+1)]
    return indices


def count_blobs_mask(mask, diagonal=False, wrap=True):
    blobs = np.zeros_like(mask, dtype=np.int32)
    blob_index = 0
    for j in range(mask.shape[1]):
        for i in range(mask.shape[0]):
            if blobs[i, j]:
                continue

            if mask[i, j]:
                blob_index += 1
                blobs[i, j] = blob_index
                outers = [(i, j)]
                while outers:
                    new_outers = []
                    for ii, jj in outers:
                        for it, jt in test_indices(ii, jj, diagonal):
                            if not wrap:
                                if it < 0 or it >= mask.shape[0] or\
                                   jt < 0 or jt >= mask.shape[1]:
                                    continue
                            else:
                                it %= mask.shape[0]
                                jt %= mask.shape[1]

                            if not blobs[it, jt] and mask[it, jt]:
                                new_outers.append((it, jt))
                                blobs[it, jt] = blob_index
                    outers = new_outers

    return blob_index, blobs


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
