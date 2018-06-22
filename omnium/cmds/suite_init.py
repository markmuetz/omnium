"""Initializes a new omnium suite, to be used in an existing rose/cylc suite"""
from logging import getLogger

from omnium.suite import Suite

logger = getLogger('om.suite_init')

ARGS = [(['--suite-type', '-t'], {'help': 'type of suite'})]


def main(suite, args):
    if args.suite_type not in Suite.suite_types:
        logger.error('--suite-type must be one of: {}', Suite.suite_types)
        return 1
    if args.suite_type == 'mirror':
        logger.error('Mirrors must be created by cloning')
        return 1
    if suite.is_init:
        logger.error('Suite already initialized')
        return 1

    suite.init('', args.suite_type)
    logger.info('Suite initialized')
