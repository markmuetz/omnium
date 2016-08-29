"""Prints config for omni"""
import os
from StringIO import StringIO

ARGS = [(['sections'], {'help': 'specify section(s) to print',
                       'nargs': '*'})]

def main(args, config):
    if args.sections:
        config_level = config
        for section in args.sections:
            if section not in config_level:
                sections_string = '/'.join(args.sections)
                msg = 'No section "{}" in config'.format(sections_string)
                raise Exception(msg)
            config_level = config_level[section]

        for k, v in config_level.items():
            print('{} = {}'.format(k, v))
    else:
        output = StringIO()
        config.write(output)
        output.seek(0)
        print(output.getvalue())
