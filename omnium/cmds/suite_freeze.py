"""Makes a suite readonly"""
from logging import getLogger

logger = getLogger('om.suite_freeze')

ARGS = []


def main(cmd_ctx, args):
    cmd_ctx.suite.freeze()
