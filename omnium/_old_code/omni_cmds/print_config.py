"""Prints config for omni"""
import os
from StringIO import StringIO

ARGS = [(['sections'], {'help': 'specify section(s) to print',
                        'nargs': '*'})]


def main(args, config, process_classes):
    from omnium.dict_printer import pprint
    from omnium.check_config import CONFIG_SCHEMA

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
        for key, value in CONFIG_SCHEMA.items():
            if isinstance(config[key], str):
                print(config[key])
            else:
                pprint({key: config[key]})
