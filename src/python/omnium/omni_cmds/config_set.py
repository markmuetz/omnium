"""Set a value in config"""
import os
from omnium.config import read_config

ARGS = [
        (['section'], {'nargs': 1, 'help': 'Section to set'}),
        (['option'], {'nargs': 1, 'help': 'Option to set'}),
        (['value'], {'nargs': 1, 'help': 'Value to use'}),
        (['--override'], {'action': 'store_true'}),
        ]

def main(args, config):
    if not hasattr(config, args.section[0]):
        raise Exception('No section {} in config'.format(args.section[0]))
    section = getattr(config, args.section[0])
    if not args.override and  hasattr(section, args.option[0]):
        raise Exception('Option {} already in section'.format(args.option[0]))
    section.set(args.option[0], args.value[0])
    config.save()
