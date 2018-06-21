"""Clones an existing omnium suite"""
from logging import getLogger

from omnium.syncher import Syncher

logger = getLogger('om.suite_init')

ARGS = [(['--host-name'], {'help': 'Short name for host', 'default': 'rdf'}),
        (['--host'], {'help': '<user>@<host_url>', 'default': 'mmuetz@login.rdf.ac.uk'}),
        (['--base-path'], {'help': 'path/to/suites', 'default': 'um10.7_runs/archive'}),
        (['--local', '-l'], {'help': 'Perform local clone', 'action': 'store_true'}),
        (['--verbose', '-v'], {'help': 'Verbose rsync', 'action': 'store_true'}),
        (['suite'], {'help': 'Suite name', 'nargs': 1})]
RUN_OUTSIDE_SUITE = True


def main(suite, args):
    logger.info('Cloning into {}', args.suite[0])
    suite.init(args.suite[0], 'mirror', args.host_name, args.host, args.base_path)
    syncher = Syncher(suite, args.local, args.host_name, args.verbose)
    syncher.clone()
    syncher.sync()
    logger.info('Suite cloned')
