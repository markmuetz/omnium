"""Converts all files given as command line args"""
import os
from logging import getLogger

from omnium.task import Task
from omnium.converter import FF2NC_Converter

logger = getLogger('om.convert')

ARGS = [(['filenames'], {'nargs': '+', 'help': 'Filename to convert'}),
        (['--delete'], {'help': 'Delete after successful conversion', 'action': 'store_true'}),
        (['--force'], {'help': 'Overwrite new file if already exists', 'action': 'store_true'}),
        (['--zlib'], {'help': 'Use compression', 'action': 'store_true'})]
RUN_OUTSIDE_SUITE = True


class Converter(FF2NC_Converter):
    single_file = True
    multi_file = False
    multi_expt = False

    input_dir = 'dummy'

    input_filename_glob = 'dummy'

    output_dir = 'dummy'
    output_filenames = ['dummy']


def main(suite, args):
    cwd = os.getcwd()
    for i, filename in enumerate(args.filenames):
        output_filename = filename + '.nc'
        task = Task(i, None, None, None, 'converter', 'ff2nc_convert',
                    [os.path.join(cwd, filename)], [os.path.join(cwd, output_filename)])
        converter = Converter(suite, task, None)
        converter.delete = args.delete
        converter.force = args.force
        converter.zlib = args.zlib
        converter.save(None, suite)
        converter.analysis_done()
