"""Makes a readonly suite readable"""
import os
import subprocess as sp

from logging import getLogger

from omnium.suite import Suite
from omnium.setup_logging import add_file_logging

logger = getLogger('om.suite_unfreeze')

ARGS = [(['suite'], {'help': 'Suite name', 'nargs': '?'})]
RUN_OUTSIDE_SUITE = True


def main(suite, args):
    if suite.is_in_suite:
        if not suite.is_readonly:
            logger.info('Suite dir is not readonly')
        suite_dir = suite.suite_dir
    else:
        suite_dir = os.path.join(os.getcwd(), args.suite)
    assert os.path.exists(suite_dir) and os.path.isdir(suite_dir)
    cmd = 'chmod -R u=rwX {}'.format(suite_dir)
    # N.B. logger is not hooked up to file.
    logger.debug(cmd)
    sp.call(cmd, shell=True)
    unfrozen_suite = Suite(suite_dir, False)
    assert not unfrozen_suite.is_readonly

    add_file_logging(unfrozen_suite.logging_filename)
    # Do once logger hooked up to file.
    logger.debug(cmd)
    logger.info('Unfrozen suite')
