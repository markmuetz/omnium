import os
from logging import getLogger

from omnium.syncher import Syncher

logger = getLogger('om.fetch')

ARGS = [(['filenames'], {'help': 'Filenames to fetch', 'nargs': '+'}),
        (['--sync', '-s'], {'help': 'Sync before fetch', 'action': 'store_true'}),
        (['--remote', '-r'], {'help': 'Remote'}),
        (['--verbose', '-v'], {'help': 'Set verbose mode', 'action': 'store_true'})]


def main(suite, args):
    syncher = Syncher(suite, remote_name=args.remote, verbose=args.verbose)

    filenames = args.filenames
    rel_filenames = []
    rel_dir = os.path.relpath(os.getcwd(), suite.suite_dir)
    rel_filenames = [os.path.join(rel_dir, fn) for fn in sorted(filenames)]
    remote_path = os.path.join(syncher.remote_base_path, suite.name)
    logger.debug('fetch from: {} ({}:{})'.format(syncher.remote_name,
                                                 syncher.remote_host,
                                                 remote_path))
    if args.sync:
        syncher.sync()
    syncher.fetch(rel_filenames)
    for filename in args.filenames:
        logger.info('Fetched {} from "{}"'.format(filename, syncher.remote_name))
