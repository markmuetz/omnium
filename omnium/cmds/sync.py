"""Syncs a mirror with a data source"""
from logging import getLogger

from omnium.syncher import Syncher

logger = getLogger('om.sync')

ARGS = [(['--remote', '-r'], {'help': 'Remote'}),
        (['--verbose', '-v'], {'help': 'Set verbose mode', 'action': 'store_true'})]


def main(suite, args):
    syncher = Syncher(suite, args.remote, verbose=args.verbose)
    syncher.sync()
