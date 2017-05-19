"""Shows useful information about a suite"""
import os
from logging import getLogger

from omnium.suite import Suite

logger = getLogger('omnium')

ARGS = []


def main(args):
    suite = Suite()
    suite.check_in_suite_dir(os.getcwd())

    logger.info('Suite: {}'.format(suite.name))
    logger.info('')
    logger.info('Suite info:')
    for line in suite.info_lines():
        logger.info(line)
    logger.info('')
    if suite.is_init:
        logger.info('Suite config:')
        for line in suite.config_lines():
            logger.info(line)
