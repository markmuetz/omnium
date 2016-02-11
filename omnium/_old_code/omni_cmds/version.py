"""Print version info"""
from omnium.version import get_version

ARGS = [(['-l', '--long'], {'help': 'print long version',
                            'action': 'store_true'})]


def main(args, config, process_classes):
    if args.long:
        print('Version ' + get_version('long'))
    else:
        print('Version ' + get_version())
