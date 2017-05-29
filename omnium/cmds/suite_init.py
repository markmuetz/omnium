"""Initializes a new omnium suite"""
import os
from logging import getLogger

from omnium.suite import Suite

logger = getLogger('omnium')


ARGS = [(['--suite-type', '-t'], {'help': 'type of suite'}),
        (['--host'], {'help': 'mmuetz@login.archer.ac.uk', 'default': 'mmuetz@login.archer.ac.uk'})]


def main(args):
    suite = Suite()
    suite.load(os.getcwd())

    if args.suite_type not in Suite.suite_types:
        logger.error('--suite-type must be one of: {}'.format(Suite.suite_types))
        return 1
    if suite.is_init:
        logger.error('Suite already initialized')
        return 1

    suite.init(args.suite_type, args.host)
    logger.info('Suite initialized')
