"""Gives info about stash variables"""
import os
import re
from logging import getLogger

logger = getLogger('omnium')

ARGS = [(['--search', '-s'], {'help': 'Search for stash var'}),
        (['--get-name', '-g'], {'help': 'Get name of stash var with code: e.g. 0,4'}),
        ]


def format_var(stash_var):
    return '{0:>3},{1:>4}: {2}'.format(stash_var[0][0], stash_var[0][1], stash_var[1])

def main(args):
    import omnium
    stash = omnium.Stash()
    if args.search:
        stash_vars = stash.search(args.search)
        for stash_var in stash_vars:
            print(format_var(stash_var))
    elif args.get_name:
        sec, item = args.get_name.split(',')
        print(stash[int(sec)][int(item)])
    else:
        print('Either --search or --get-name')
