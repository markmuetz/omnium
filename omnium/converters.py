import os
import re
import abc
from logging import getLogger
from itertools import izip

import numpy as np
import iris

from omnium.omnium_errors import OmniumError
from omnium.utils import get_cube

logger = getLogger('omnium')


class Converter(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, overwrite=False, delete=False, verify=False, allow_non_standard=False,
                 zlib=True):
        self.overwrite = overwrite
        self.delete = delete
        self.verify = verify
        self.allow_non_standard = allow_non_standard
        self.zlib = zlib

    def _converted_filename(self, old_filename):
        dirname = os.path.dirname(old_filename)
        filename = os.path.basename(old_filename)

        if not self.allow_non_standard:
            for pattern in self.standard_patterns:
                match = re.match(pattern, filename)

                if match:
                    logger.debug('matched {} with {}'.format(filename, pattern))
                    break

            if not match:
                raise OmniumError('Filename not standard: {}'.format(filename))

        newname = filename + '.nc'
        return os.path.join(dirname, newname)

    @abc.abstractmethod
    def _convert(self, filename, converted_filename):
        return

    def convert(self, filename):
        self.messages = ['archer_analysis convert ' + self.name]
        converted_filename = self._converted_filename(filename)
        logger.info('Convert: {} -> {}'.format(filename, converted_filename))

        if os.path.exists(converted_filename):
            if self.overwrite:
                logger.info('Deleting: {}'.format(converted_filename))
                self.messages.append('Deleting: {}'.format(converted_filename))
                os.remove(converted_filename)
            elif not os.path.exists(converted_filename + '.done'):
                # Could have been a problem creating file *or*
                # could still be being written.
                logger.info('Already converted but:')
                logger.warn('No .done file: {}'.format(converted_filename))
                return converted_filename
            else:
                logger.info('Already converted')
                return converted_filename

        self.messages.append('Original filename: {}'.format(filename))
        self.messages.append('New filename: {}'.format(converted_filename))

        self._convert(filename, converted_filename)

        if self.delete:
            logger.info('Delete: {}'.format(filename))
            os.remove(filename)
            self.messages.append('Deleted original')

        with open(converted_filename + '.done', 'w') as f:
            logger.debug('Writing ' + converted_filename + '.done')
            f.write('\n'.join(self.messages))
            f.write('\n')

        return converted_filename


class FF2NC(Converter):
    """Convert from Fields File (often .pp? extension) to NetCDF4 using iris"""
    name = 'ff2nc'
    standard_patterns = ['.*\.pp\d', '^atmosa_da(?P<ts>\d{3}$)']
    out_ext = '.nc'

    def _convert(self, filename, converted_filename):
        self.messages.append('Using iris to convert')
        cubes = iris.load(filename)
        if len(cubes) == 0:
            logger.warn('{} contains no data'.format(filename))
        else:
            logger.debug('Saving data to:{} (zlib={})'.format(converted_filename, self.zlib))
            # Use default compression: complevel 4.
            iris.save(cubes, converted_filename, zlib=self.zlib)

        if self.verify:
            logger.info('Verifying')
            # Check converted cubes are identical to originals.
            # Done in the _convert (i.e. derived impl.) because this way I don't have
            # to reload the data.
            converted_cubes = iris.load(converted_filename)
            for cube in cubes:
                logger.debug('Verify {}'.format(cube.name()))
                stash = cube.attributes['STASH']
                conv_cube = get_cube(converted_cubes, stash.section, stash.item)

                # Make cube iterators and slice over all but first dim.
                cube_it = cube.slices(range(1, cube.ndim))
                conv_cube_it = conv_cube.slices(range(1, conv_cube.ndim))

                # zip iterators together, grabbing slices and comparing them.
                for cslice, conv_cslice in izip(cube_it, conv_cube_it):
                    if not np.all(cslice.data == conv_cslice.data):
                        logger.error('Cubes not equal')
                        logger.error('Cube: {}'.format(cslice.name()))
                        logger.error('Time: {}'.format(cslice.coord('time')))
                        raise OmniumError('Mismatch in data between cubes')
            logger.info('Verified')


CONVERTERS = {
    FF2NC.name: FF2NC,
}
