"""Makes a readonly suite readable"""
import os
import subprocess as sp

from logging import getLogger

from omnium.suite import Suite
from omnium.setup_logging import add_file_logging

logger = getLogger('om.suite_unfreeze')

ARGS = [(['suite'], {'help': 'Suite name', 'nargs': '?'})]
RUN_OUTSIDE_SUITE = True


def main(cmd_ctx, args):
    if cmd_ctx.suite.is_in_suite:
        if not cmd_ctx.suite.is_readonly:
            logger.info('Suite dir is not readonly')
        cmd_ctx.suite.unfreeze()
    else:
        suite_dir = os.path.join(os.getcwd(), args.cmd_ctx.suite)
        cmd_ctx.suite.unfreeze(suite_dir)
