"""Perform consistency checks on config"""
from logging import getLogger

from omnium.check_config import ConfigChecker

logger = getLogger('omni')

ARGS = [(['--warnings-as-errors'], {'help': 'Treat all warnings as errors',
                                    'action': 'store_true',
                                    'default': False})]


def main(args, config, process_classes):
    checker = ConfigChecker(config, process_classes, False,
                            args.warnings_as_errors)
    warnings, errors = checker.run_checks()
    if warnings:
        logger.warn('Config Warnings:')
        for warning in warnings:
            logger.warn(warning)

    if errors:
        logger.error('CONFIG ERRORS FOUND:')
        for error in errors:
            logger.error(error.message)
            if error.hint:
                logger.error(error.hint)
    else:
        logger.info('Config OK')
