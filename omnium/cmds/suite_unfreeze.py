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
        suite.unfreeze()
    else:
        suite_dir = os.path.join(os.getcwd(), args.suite)
        suite.unfreeze(suite_dir)
