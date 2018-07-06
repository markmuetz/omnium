import os
import re
from logging import getLogger

import iris
import numpy as np
from omnium.analyser import Analyser
from omnium.omnium_errors import OmniumError
from omnium.utils import get_cube

logger = getLogger('om.converters')


class FF2NC_Converter(Analyser):
    analysis_name = 'ff2nc_converter'
    single_file = True
    input_dir = 'work/20000101T0000Z/{expt}_atmos'
    input_filename = '{input_dir}/atmos.pp1'
    output_dir = 'work/20000101T0000Z/{expt}_atmos'
    output_filenames = ['{output_dir}/atmos.pp1.nc']

    zlib = True
    force = False
    delete = False
    verify = False

    def do_verify(self, converted_filename):
        logger.info('Verifying')
        # Check converted cubes are identical to originals.
        # Done in the _convert (i.e. derived impl.) because this way I don't have
        # to reload the data.
        converted_cubes = iris.load(converted_filename)
        for cube in self.cubes:
            logger.debug('Verify {}', cube.name())
            stash = cube.attributes['STASH']
            conv_cube = get_cube(converted_cubes, stash.section, stash.item)

            # Make cube iterators and slice over all but first dim.
            cube_it = cube.slices(range(1, cube.ndim))
            conv_cube_it = conv_cube.slices(range(1, conv_cube.ndim))

            # zip iterators together, grabbing slices and comparing them.
            for cslice, conv_cslice in zip(cube_it, conv_cube_it):
                if not np.all(cslice.data == conv_cslice.data):
                    logger.error('Cubes not equal')
                    logger.error('Cube: {}', cslice.name())
                    logger.error('Time: {}', cslice.coord('time'))
                    raise OmniumError('Mismatch in data between cubes')
        logger.info('Verified')

    def load(self):
        pass

    def run(self):
        pass

    def save(self, state=None, suite=None):
        self.messages = ['archer_analysis convert ' + self.analysis_name]
        input_filename = self.task.filenames[0]
        converted_filename = self.task.output_filenames[0]
        logger.info('Convert: {} -> {}', input_filename, converted_filename)

        if os.path.exists(converted_filename):
            if self.force:
                logger.info('Deleting: {}', converted_filename)
                self.messages.append('Deleting: {}'.format(converted_filename))
                os.remove(converted_filename)
            elif not os.path.exists(converted_filename + '.done'):
                # Could have been a problem creating file *or*
                # could still be being written.
                logger.info('Already converted but:')
                logger.warning('No .done file: {}', converted_filename)
                return converted_filename
            else:
                logger.info('Already converted')
                return converted_filename

        self.cubes = iris.load(input_filename)

        self.messages.append('Original filename: {}'.format(input_filename))
        self.messages.append('New filename: {}'.format(converted_filename))

        if len(self.cubes) == 0:
            logger.warning('{} contains no data', input_filename)
        else:
            logger.debug('Saving data to:{} (zlib={})', converted_filename, self.zlib)
            # Use default compression: complevel 4.
            iris.save(self.cubes, converted_filename, zlib=self.zlib)

        if self.verify:
            self.do_verify(converted_filename)

        if self.delete:
            logger.info('Delete: {}', input_filename)
            os.remove(input_filename)
            self.messages.append('Deleted original')

        return converted_filename
