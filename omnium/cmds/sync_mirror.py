"""Syncs a mirror with a data source"""
import os
from logging import getLogger

from omnium.omnium_errors import OmniumError
from omnium.syncher import Syncher
from omnium.suite import Suite

logger = getLogger('omnium')

ARGS = [(['--host'], {'help': 'mmuetz@login.archer.ac.uk', 'default': None}),
        (['--create', '-c'], {'help': 'u-AAXXX'}),
        (['--base-path', '-b'], {'help': 'Base path on remote computer',
                                 'default': 'work/cylc-run'}),
        (['--verbose', '-v'], {'help': 'Set verbose mode', 'action': 'store_true'}),
        (['exts'], {'help': 'Additional extensions to include (e.g. .png .pp1.nc)', 'nargs': '*'})]


def main(args):
    suite = Suite()
    try:
        suite.load(os.getcwd())
    except OmniumError:
        pass

    if suite.is_in_suite:
        if args.create:
            logger.error('Cannot use --create from within a suite')
            return 1
        if not suite.is_init:
            logger.error('Suite has not been initialized')
            return 1
        suite_type = suite.suite_config['settings']['suite_type']
        if not suite_type == 'mirror':
            logger.error('Suite is not a mirror, is: {}'.format(suite_type))
            return 1

        suite_name = suite.name
    else:
        if not args.create:
            logger.error('Must be called from within a suite or with --create')
            return 1
        else:
            suite_name = args.create
            if os.path.exists(suite_name):
                logger.error('Mirror {} already exists'.format(suite_name))
                return 1

    if not args.host and args.create:
        host = 'mmuetz@login.archer.ac.uk'
    else:
        host = args.host

    syncher = Syncher(suite, host, args.base_path, args.verbose)
    # Extend with any exts passed by user.
    syncher.add_exts(args.exts)

    if args.create:
        syncher.create(suite_name)
        # create <suite>/.omnium/suite.conf etc.
        suite.load(os.path.join(os.getcwd(), suite_name))
        suite.init('mirror', args.host)
    else:
        syncher.sync()
