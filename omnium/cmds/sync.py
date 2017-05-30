"""Syncs a mirror with a data source"""
import os
from logging import getLogger

from omnium.omnium_errors import OmniumError
from omnium.syncher import Syncher
from omnium.suite import Suite

logger = getLogger('omnium')

ARGS = [(['--remote', '-r'], {'help': 'Remote'}),
        (['--verbose', '-v'], {'help': 'Set verbose mode', 'action': 'store_true'})]


def main(args):
    suite = Suite()
    try:
        suite.load(os.getcwd())
    except OmniumError:
        pass

    syncher = Syncher(suite, args.remote, args.verbose)
    syncher.sync()
