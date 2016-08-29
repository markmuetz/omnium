"""Set a value in config"""
import os

ARGS = [
        (['sections'], {'nargs': '*', 'help': 'Section(s) to set'}),
        (['option'], {'nargs': 1, 'help': 'Option to set'}),
        (['value'], {'nargs': 1, 'help': 'Value to use'}),
        (['--override'], {'action': 'store_true'}),
        ]

def main(args, config):
    config_level = config
    for section in args.sections:
        if section not in config_level:
            sections_string = '/'.join(args.sections)
            msg = 'No section "{}" in config'.format(sections_string)
            raise Exception(msg)
        config_level = config_level[section]

    config_level[args.option[0]] = args.value[0]
    config.write()
