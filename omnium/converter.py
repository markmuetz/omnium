import os
import re
from logging import getLogger
from itertools import izip

import numpy as np
import iris

from omnium.analyser import Analyser
from omnium.omnium_errors import OmniumError
from omnium.utils import get_cube

logger = getLogger('om.converters')


class FF2NC_Converter(Analyser):
    analysis_name = 'ff2nc_converter'
    standard_patterns = ['.*\.pp\d', '^atmosa_da(?P<ts>\d{3}$)']
    out_ext = '.nc'

    @classmethod
    def _converted_filename(cls, old_filename):
        dirname = os.path.dirname(old_filename)
        filename = os.path.basename(old_filename)

        for pattern in cls.standard_patterns:
            match = re.match(pattern, filename)

            if match:
                logger.debug('matched {} with {}'.format(filename, pattern))
                break

        if not match:
            raise OmniumError('Filename not standard: {}'.format(filename))

        newname = filename + '.nc'
        return os.path.join(dirname, newname)

    def set_config(self, config):
        super(FF2NC_Converter, self).set_config(config)
        self.overwrite = config.getboolean('overwrite', False)
        self.delete = config.getboolean('delete', False)
        self.zlib = config.getboolean('zlib', True)
        self.verify = config.getboolean('verify', False)

    def do_verify(self, converted_filename):
        logger.info('Verifying')
        # Check converted cubes are identical to originals.
        # Done in the _convert (i.e. derived impl.) because this way I don't have
        # to reload the data.
        converted_cubes = iris.load(converted_filename)
        for cube in self.cubes:
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

    def load(self):
        pass

    def run_analysis(self):
        pass

    def save(self, state=None, suite=None):
        self.messages = ['archer_analysis convert ' + self.analysis_name]
        converted_filename = self._converted_filename(self.filename)
        logger.info('Convert: {} -> {}'.format(self.filename, converted_filename))

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

        self.cubes = iris.load(self.filename)

        self.messages.append('Original filename: {}'.format(self.filename))
        self.messages.append('New filename: {}'.format(converted_filename))

        if len(self.cubes) == 0:
            logger.warn('{} contains no data'.format(self.filename))
        else:
            logger.debug('Saving data to:{} (zlib={})'.format(converted_filename, self.zlib))
            # Use default compression: complevel 4.
            iris.save(self.cubes, converted_filename, zlib=self.zlib)

        if self.verify:
            self.do_verify(converted_filename)

        if self.delete:
            logger.info('Delete: {}'.format(self.filename))
            os.remove(self.filename)
            self.messages.append('Deleted original')

        with open(converted_filename + '.done', 'w') as f:
            logger.debug('Writing ' + converted_filename + '.done')
            f.write('\n'.join(self.messages))
            f.write('\n')

        return converted_filename
