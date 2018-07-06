"""Converts all files given as command line args"""
import os
from logging import getLogger

from omnium.task import Task

logger = getLogger('om.convert')

ARGS = [(['filenames'], {'nargs': '+', 'help': 'Filename to convert'}),
        (['--delete'], {'help': 'Delete after successful conversion', 'action': 'store_true'}),
        (['--force'], {'help': 'Overwrite new file if already exists', 'action': 'store_true'}),
        (['--zlib'], {'help': 'Use compression', 'action': 'store_true'})]
RUN_OUTSIDE_SUITE = True


def main(suite, args):
    from omnium.converter import FF2NC_Converter
    cwd = os.getcwd()
    for i, filename in enumerate(args.filenames):
        output_filename = filename + '.nc'
        task = Task(i, None, None, None, 'converter', 'ff2nc_convert',
                    [os.path.join(cwd, filename)], [os.path.join(cwd, output_filename)])
        converter = FF2NC_Converter(suite, task, None)
        converter.delete = args.delete
        converter.force = args.force
        converter.zlib = args.zlib
        converter.save(None, suite)
        converter.analysis_done()
