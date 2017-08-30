"""Shows useful information about a suite"""
import os
from logging import getLogger

from omnium.suite import Suite

logger = getLogger('om.suite_info')

ARGS = []


def main(suite, args):
    logger.info('Suite: {}'.format(suite.name))
    logger.info('')
    logger.info('Suite info:')
    for line in suite.info_lines():
        logger.info(line)
    logger.info('')
    if suite.is_init:
        logger.info('Suite config:')
        for line in suite.suite_config_lines():
            logger.info(line)
