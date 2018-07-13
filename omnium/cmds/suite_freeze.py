"""Makes a suite readonly"""
from logging import getLogger

logger = getLogger('om.suite_freeze')

ARGS = []


def main(suite, args):
    suite.freeze()
