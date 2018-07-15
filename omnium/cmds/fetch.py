"""Fetches a file, files or dir from remote suite"""
import os
from logging import getLogger

from omnium.omnium_errors import OmniumError
from omnium.syncher import Syncher

logger = getLogger('om.fetch')

ARGS = [(['filenames'], {'help': 'Filenames to fetch', 'nargs': '+'}),
        (['--sync', '-s'], {'help': 'Sync before fetch', 'action': 'store_true'}),
        (['--remote', '-r'], {'help': 'Remote'}),
        (['--verbose', '-v'], {'help': 'Set verbose mode', 'action': 'store_true'})]


def main(cmd_ctx, args):
    syncher = Syncher(cmd_ctx.suite, remote_name=args.remote, verbose=args.verbose)

    filenames = args.filenames
    rel_dir = os.path.relpath(os.getcwd(), cmd_ctx.suite.suite_dir)
    rel_filenames = [os.path.join(rel_dir, fn) for fn in sorted(filenames)]
    remote_path = os.path.join(syncher.remote_base_path, cmd_ctx.suite.name)
    logger.debug('fetch from: {} ({}:{})', syncher.remote_name, syncher.remote_host, remote_path)
    if args.sync:
        syncher.sync()
    syncher.fetch(rel_filenames)
    for filename in args.filenames:
        if cmd_ctx.suite.check_filename_missing(filename):
            raise OmniumError('Filename {} not fetched'.format(filename))
        logger.info('Fetched {} from "{}"', filename, syncher.remote_name)
