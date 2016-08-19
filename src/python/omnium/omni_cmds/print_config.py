"""Prints config for omni"""
import os

ARGS = [(['--section'], {'help': 'specify section to print'})]

def main(args, config):
    if args.section:
        if not hasattr(config, args.section):
            raise Exception('No section {} in config'.format(args.section))
        section = getattr(config, args.section)
        print(section)
    else:
        print(config)
