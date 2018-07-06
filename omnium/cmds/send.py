"""Sends a file or files to remote suite"""
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
            logger.warning('Included symlink {}', filename)
        else:
            rel_filenames.append(os.path.join(rel_dir, filename))

    syncher.send(rel_filenames)
    for filename in args.filenames:
        logger.info('Sent {} to "{}"', filename, syncher.remote_name)
