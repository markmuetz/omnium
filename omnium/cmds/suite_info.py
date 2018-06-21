"""Shows useful information about a suite"""
from logging import getLogger

logger = getLogger('om.suite_info')

ARGS = []


def main(suite, args):
    logger.info('Suite: {}', suite.name)
    logger.info('')
    logger.info('Suite info:')
    for line in suite.info_lines():
        logger.info(line)
    logger.info('')
    if suite.is_init:
        logger.info('Suite config:')
        for line in suite.suite_config_lines():
            logger.info(line)
