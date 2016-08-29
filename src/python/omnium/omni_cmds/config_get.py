"""Get a value from config"""
import os

ARGS = [
        (['sections'], {'nargs': '*',
                       'help': 'Section(s) to get value for'}),
        (['option'], {'nargs': 1,
                       'help': 'Option to get value for'}),
        ]

def main(args, config):
    config_level = config
    for section in args.sections:
        if section not in config_level:
            sections_string = '/'.join(args.sections)
            msg = 'No section "{}" in config'.format(sections_string)
            raise Exception(msg)
        config_level = config_level[section]

    print(config_level[args.option[0]])
