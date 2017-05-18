"""Converts all files given as command line args"""
import os
import re
from logging import getLogger

logger = getLogger('omnium')

ARGS = [(['filenames'], {'nargs': '+', 'help': 'Filename to convert'}),
        (['--converter', '-c'], {'help': 'Converter to use', 'default': 'ff2nc'}),
        (['--delete'], {'help': 'Delete after successful conversion', 'action': 'store_true'}),
        (['--allow-non-ppX'], {'help': 'Allow conversion of files not ending in .pp?', 'action': 'store_true'}),
        (['--overwrite'], {'help': 'Overwrite new file if already exists', 'action': 'store_true'})]


def main(args):
    import iris
    from omnium.converters import CONVERTERS
    converter = CONVERTERS[args.converter](args.overwrite, args.delete, args.allow_non_ppX)

    for filename in args.filenames:
        converter.convert(filename)
