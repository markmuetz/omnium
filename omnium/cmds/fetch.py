import os
from glob import glob
from logging import getLogger

from omnium.syncher import Syncher
from omnium.suite import Suite

logger = getLogger('om.fetch')

ARGS = [(['filenames'], {'help': 'Filenames to fetch', 'nargs': '+'}),
        (['--sync', '-s'], {'help': 'Sync before fetch', 'action': 'store_true'}),
        (['--remote', '-r'], {'help': 'Remote'}),
        (['--verbose', '-v'], {'help': 'Set verbose mode', 'action': 'store_true'})]


def main(suite, args):
    syncher = Syncher(suite, args.remote, args.verbose)

    filenames = args.filenames
    rel_filenames = []
    rel_dir = os.path.relpath(os.getcwd(), suite.suite_dir)
    rel_filenames = [os.path.join(rel_dir, fn) for fn in sorted(filenames)]
    logger.debug('fetch from: {} ({}:{})'.format(syncher.remote_name, 
                                                 syncher.remote_host,
                                                 os.path.join(syncher.remote_base_path, suite.name)))
    if args.sync:
        syncher.sync()
    syncher.fetch(rel_filenames)
    for filename in args.filenames:
        logger.info('Fetched {} from "{}"'.format(filename, syncher.remote_name))
