"""Syncs a mirror with a data source"""
from logging import getLogger

from omnium.syncher import Syncher
from omnium.omnium_errors import OmniumError

logger = getLogger('om.sync')

ARGS = [(['--remote', '-r'], {'help': 'Remote'}),
        (['--verbose', '-v'], {'help': 'Set verbose mode', 'action': 'store_true'})]


def main(cmd_ctx, args):
    if cmd_ctx.suite.suite_config['settings']['suite_type'] != 'mirror':
        raise OmniumError('Sync can only be used with a suite that is a mirror')
    syncher = Syncher(cmd_ctx.suite, args.remote, verbose=args.verbose)
    syncher.sync()
