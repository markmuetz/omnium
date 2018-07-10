"""Makes a suite readonly"""
import os
import subprocess as sp

from logging import getLogger

logger = getLogger('om.suite_freeze')

ARGS = []


def main(suite, args):
    cmd = 'chmod -R u=rX {}'.format(suite.suite_dir)
    logger.debug(cmd)
    logger.info('Suite frozen: no more commands can be run in suite')
    unfreeze_cmd = 'omnium suite-unfreeze {}'.format(suite.suite_dir)
    logger.info('No dirs/files can be created/edited/deleted without running `{}`', unfreeze_cmd)
    sp.call(cmd, shell=True)
