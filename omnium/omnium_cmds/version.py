"""Print version info"""
import os
from omnium.version import get_version

ARGS = [(['-l', '--long'], {'help': 'print long version',
                            'action': 'store_true'})]


def main(args):
    if args.long:
        print('Version ' + get_version('long'))
    else:
        print('Version ' + get_version())
