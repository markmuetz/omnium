import os
from logging import getLogger

from omnium.syncher import Syncher

logger = getLogger('om.send')

ARGS = [(['filenames'], {'help': 'Filenames to send', 'nargs': '+'}),
        (['--remote', '-r'], {'help': 'Remote'}),
        (['--verbose', '-v'], {'help': 'Set verbose mode', 'action': 'store_true'})]


def main(suite, args):
    syncher = Syncher(suite, args.remote, args.verbose)

    filenames = args.filenames
    rel_dir = os.path.relpath(os.getcwd(), suite.suite_dir)
    rel_filenames = []
    for filename in filenames:
        if os.path.islink(filename):
            logger.warn('Included symlink {}'.format(filename))
        else:
            rel_filenames.append(os.path.join(rel_dir, filename))

    syncher.send(rel_filenames)
