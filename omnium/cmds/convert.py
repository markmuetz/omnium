"""Converts all files given as command line args"""
import os
import re
from logging import getLogger

logger = getLogger('omnium')

ARGS = [(['filenames'], {'nargs': '+', 'help': 'Filename to convert'}),
        (['--converter', '-c'], {'help': 'Converter to use', 'default': 'ff2nc'}),
        (['--delete'], {'help': 'Delete after successful conversion', 'action': 'store_true'}),
        (['--allow-non-standard'], {'help': 'Allow conversion of non-standard files',
                                    'action': 'store_true'}),
        (['--overwrite'], {'help': 'Overwrite new file if already exists', 'action': 'store_true'}),
        (['--zlib'], {'help': 'Use compression', 'action': 'store_true'})]


def main(args):
    import iris
    from omnium.converters import CONVERTERS
    converter = CONVERTERS[args.converter](args.overwrite, args.delete,
                                           args.allow_non_standard, args.zlib)

    for filename in args.filenames:
        converter.convert(filename)
