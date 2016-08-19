"""Deletes section or option from config"""
import os
from omnium.config import read_config

ARGS = [
        (['section'], {'nargs': 1, 'help': 'Section to set'}),
        (['option'], {'nargs': '?', 'help': 'Option to set'}),
        ]

def main(args, config):
    if not hasattr(config, args.section[0]):
        raise Exception('No section {} in config'.format(args.section[0]))
    section = getattr(config, args.section[0])
    if args.option:
        if not hasattr(section, args.option[0]):
            raise Exception('No option {} in section'.format(args.option[0]))

        sec_opt = '[{}]/{}'.format(args.section[0], args.option[0])
        msg = 'Are you sure you want to delete {} (y/[n]): '.format(sec_opt)
        r = raw_input(msg)
        if r == 'y':
            section.delete(args.option[0])
            config.save()
            print('{} deleted.'.format(sec_opt))
        else:
            print('{} not deleted.'.format(sec_opt))
    else:
        # Deleting section.
        sec = '[{}]'.format(args.section[0])
        msg = 'Are you sure you want to delete section {} (y/[n]): '.format(sec)
        r = raw_input(msg)
        if r == 'y':
            config.delete(args.section[0])
            config.save()
            print('{} deleted.'.format(sec))
        else:
            print('{} not deleted.'.format(sec))

