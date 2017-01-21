"""Converts all files given as command line args"""
import os
import re
from logging import getLogger

logger = getLogger('omni')

ARGS = [(['filenames'], {'nargs': '+', 'help': 'Filename to convert'}),
        (['--converter', '-c'], {'help': 'Converter to use', 'default': 'ff2nc'}),
        (['--delete'], {'help': 'Delete after successful conversion', 'action': 'store_true'}),
        (['--overwrite'], {'help': 'Overwrite new file if already exists', 'action': 'store_true'})]


def convert_ff2nc_filename(filepath):
    # e.g. atmos.000.pp3 => atmos.000.pp3.nc
    # Who knows why they give a fields file the extension pp??
    dirname = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    if not re.match('pp\d', filename[-3:]):
        raise Exception('Unrecognized filename {}'.format(filename))

    newname = filename + '.nc'
    return os.path.join(dirname, newname)


def main(args):
    import iris
    for filename in args.filenames:
        messages = []
        messages.append('Using iris to convert')
        messages.append('Original filename: {}'.format(filename))
        #logger.debug(filename)
        messages.append('Using converter {}'.format(args.converter))
        if args.converter == 'ff2nc':
            converted_filename = convert_ff2nc_filename(filename)

        if os.path.exists(converted_filename):
            if args.overwrite:
                messages.append('Deleting: {}'.format(converted_filename))
                os.remove(converted_filename)
            else:
                raise Exception('File {} already exists'.format(converted_filename))

        messages.append('New filename: {}'.format(converted_filename))
        print('Convert: {} -> {}'.format(filename, converted_filename))

        cubes = iris.load(filename)
        iris.save(cubes, converted_filename)

        if args.delete:
            print('Delete: {}'.format(filename))
            os.remove(filename)
            messages.append('Deleted original')

        with open(converted_filename + '.done', 'w') as f:
            f.write('\n'.join(messages))
            f.write('\n')
