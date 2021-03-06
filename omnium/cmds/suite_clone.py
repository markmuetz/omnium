"""Clones an existing omnium suite"""
from logging import getLogger

from omnium.syncher import Syncher

logger = getLogger('om.suite_clone')

ARGS = [(['--host-name'], {'help': 'Short name for host', 'default': 'rdf'}),
        (['--host'], {'help': '<user>@<host_url> or localhost', 'default': 'localhost'}),
        (['--base-path'], {'help': 'path/to/suites'}),
        (['--verbose', '-v'], {'help': 'Verbose rsync', 'action': 'store_true'}),
        (['suite'], {'help': 'Suite name', 'nargs': 1})]
RUN_OUTSIDE_SUITE = True


def main(cmd_ctx, args):
    logger.info('Cloning into {}', args.suite[0])
    cmd_ctx.suite.init(args.suite[0], 'mirror', args.host_name, args.host, args.base_path)
    syncher = Syncher(cmd_ctx.suite, args.host_name, args.verbose)
    syncher.clone()
    syncher.sync()
    logger.info('Suite cloned')
