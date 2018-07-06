"""Clones an existing omnium suite"""
from logging import getLogger

from omnium.syncher import Syncher

logger = getLogger('om.suite_init')

ARGS = [(['--host-name'], {'help': 'Short name for host', 'default': 'rdf'}),
        (['--host'], {'help': '<user>@<host_url> or localhost', 'default': 'localhost'}),
        (['--base-path'], {'help': 'path/to/suites'}),
        (['--verbose', '-v'], {'help': 'Verbose rsync', 'action': 'store_true'}),
        (['suite'], {'help': 'Suite name', 'nargs': 1})]
RUN_OUTSIDE_SUITE = True


def main(suite, args):
    logger.info('Cloning into {}', args.suite[0])
    suite.init(args.suite[0], 'mirror', args.host_name, args.host, args.base_path)
    syncher = Syncher(suite, args.host_name, args.verbose)
    syncher.clone()
    syncher.sync()
    logger.info('Suite cloned')
