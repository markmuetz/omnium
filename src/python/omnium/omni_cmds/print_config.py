"""Prints config for omni"""
import os
from StringIO import StringIO

from omnium.dict_printer import pprint

ARGS = [(['sections'], {'help': 'specify section(s) to print',
                       'nargs': '*'})]


def main(args, config):
    if args.sections:
        config_level = config
        for section in args.sections:
            if section not in config_level:
                sections_string = ' '.join(args.sections)
                msg = 'No section "{}" in config'.format(sections_string)
                raise Exception(msg)
            config_level = config_level[section]

        if hasattr(config_level, 'iteritems'):
            pprint(config_level)
        else:
            print(config_level)
    else:
        pprint(config)
