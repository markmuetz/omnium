"""Get a value from config"""
import os
from omnium.config import read_config

ARGS = [
        (['section'], {'nargs': 1,
                       'help': 'Section to get value for'}),
        (['option'], {'nargs': 1,
                       'help': 'Option to get value for'}),
        ]

def main(args, config):
    if not hasattr(config, args.section[0]):
        raise Exception('No section {} in config'.format(args.section[0]))
    section = getattr(config, args.section[0])
    if not hasattr(section, args.option[0]):
        raise Exception('No option {} in section'.format(args.option[0]))
    value = getattr(section, args.option[0])

    print(value)
