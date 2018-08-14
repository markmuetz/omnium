"""Initializes a new omnium suite, to be used in an existing rose/cylc suite"""
from logging import getLogger

from omnium import OmniumError
from omnium.suite import Suite

logger = getLogger('om.suite_init')

ARGS = [(['--suite-type', '-t'], {'help': 'type of suite'})]
RUN_OUTSIDE_SUITE = True


def main(cmd_ctx, args):
    if args.suite_type not in Suite.suite_types:
        logger.error('--suite-type must be one of: {}', Suite.suite_types)
        return 1
    if args.suite_type == 'mirror':
        logger.error('Mirrors must be created by cloning')
        raise OmniumError('Mirrors must be created by cloning')
    if cmd_ctx.suite.is_init:
        logger.error('Suite already initialized')
        raise OmniumError('Suite already initialized')

    cmd_ctx.suite.init('', args.suite_type)
    logger.info('Suite initialized')
