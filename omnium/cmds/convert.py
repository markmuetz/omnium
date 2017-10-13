"""Converts all files given as command line args"""
import os
from logging import getLogger

from configparser import ConfigParser
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
    cp = ConfigParser()
    cp.add_section('convert')
    cp.set('convert', 'delete', str(args.delete))
    cp.set('convert', 'force', str(args.force))
    cp.set('convert', 'zlib', str(args.zlib))

    for i, filename in enumerate(args.filenames):
        task = Task(i, None, None, None, 'converter', 'ff2nc_convert', 'ff2nc_convert',
                    [filename], ['dummy_output_name'])
        converter = FF2NC_Converter(suite, task, cwd, None)
        converter.set_config(cp['convert'])
        converter.save(None, suite)
