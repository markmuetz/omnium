"""Entry point into running omnium from command line

all commands are run as:
    omnium [omnium_opts] <cmd> [cmd_opts] [cmd_args]
"""
import os
from logging import getLogger

import omnium
import omnium.cmds as cmds
from omnium.analysis import AnalysisPkgs
from omnium.cmds.cmd_context import CmdContext
from omnium.command_parser import parse_commands
from omnium.pkg_state import PkgState
from omnium.setup_logging import setup_logger, add_file_logging
from omnium.suite import Suite

# Top level args, e.g. omnium -D ...
ARGS = [(['--throw-exceptions', '-X'], {'action': 'store_true', 'default': False}),
        (['--DEBUG', '-D'], {'action': 'store_true', 'default': False}),
        (['--suite-dir', '-s'], {'help': 'Suite directory'}),
        (['--bw-logs', '-b'], {'action': 'store_true', 'default': False})]


def main(argv, import_log_msg=''):
    "Parse commands/env, setup logging, dispatch to cmds/<cmd>.py"
    matplotlib_logger = getLogger('matplotlib')
    matplotlib_logger.setLevel('WARNING')

    omnium_cmds, args = parse_commands('omnium', ARGS, cmds, argv[1:])
    cmd = omnium_cmds[args.cmd_name]

    env_debug = os.getenv('OMNIUM_DEBUG') == 'True'
    cylc_control = os.getenv('CYLC_CONTROL') == 'True'
    omnium_dev = os.getenv('OMNIUM_DEV') == 'True'

    if args.DEBUG or env_debug:
        debug = True
    else:
        debug = False

    if cylc_control:
        colour = False
        warn_stderr = True
    else:
        colour = not args.bw_logs
        warn_stderr = False

    logger = setup_logger(debug, colour, warn_stderr)

    if args.suite_dir:
        logger.debug('orig dir: {}', os.getcwd())
        os.chdir(args.suite_dir)
    elif cylc_control:
        suite_base_dir = os.getenv('OMNIUM_BASE_SUITE_DIR')
        cylc_suite_name = os.getenv('CYLC_SUITE_NAME')

        logger.debug('orig dir: {}', os.getcwd())
        suite_dir = os.path.join(suite_base_dir, cylc_suite_name)
        os.chdir(suite_dir)

    omnium_analysis_pkgs = os.getenv('OMNIUM_ANALYSIS_PKGS')
    if omnium_analysis_pkgs:
        analysis_pkg_names = omnium_analysis_pkgs.split(':')
    else:
        analysis_pkg_names = []

    logger.debug('start dir: {}', os.getcwd())
    suite = Suite(os.getcwd(), cylc_control)
    if not suite.is_in_suite:
        if not getattr(cmd, 'RUN_OUTSIDE_SUITE', False):
            logger.error('Not in an omnium suite')
            return
    else:
        if not suite.is_readonly:
            if hasattr(cmd, 'get_logging_filename'):
                logging_filename = cmd.get_logging_filename(suite, args)
            else:
                logging_filename = suite.logging_filename
            add_file_logging(logging_filename)

    analysis_pkgs = AnalysisPkgs(analysis_pkg_names)
    suite.set_analysis_pkgs(analysis_pkgs)

    if omnium_dev:
        logger.info('running omnium_dev')
        logger.info(omnium)
    logger.debug('omnium import: {}', import_log_msg)
    logger.debug(' '.join(argv))
    logger.debug(args)
    logger.debug(args.cmd_name)
    logger.debug('cylc_control: {}', cylc_control)

    omnium_state = PkgState(omnium)
    logger.debug('omnium state: {}', omnium_state)

    cmd_ctx = CmdContext(omnium_state, analysis_pkgs, suite)
    if not args.throw_exceptions:
        logger.debug('Catching all exceptions')
        try:
            # dispatch on arg
            return cmd.main(cmd_ctx, args)
        except Exception as e:
            logger.exception('{}', e)
            raise
    else:
        return cmd.main(cmd_ctx, args)
