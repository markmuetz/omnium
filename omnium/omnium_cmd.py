"""Entry point into running omnium from command line

all commands are run as:
    omnium <cmd> <cmd_opts>
"""
import os
import sys

from command_parser import parse_commands
from setup_logging import setup_logger
import cmds

# Top level args, e.g. omnium -D ...
ARGS = [(['--throw-exceptions', '-x'], {'action': 'store_true', 'default': False}),
        (['--DEBUG', '-D'], {'action': 'store_true', 'default': False}),
        (['--bw-logs', '-b'], {'action': 'store_true', 'default': False})]


def main(argv, import_log_msg=''):
    "Parse commands/env, setup logging, dispatch to cmd/<cmd>.py"
    omnium_cmds, args = parse_commands('omnium', ARGS, cmds, argv[1:])

    env_debug = os.getenv('OMNIUM_DEBUG') == 'True'
    cylc_control = os.getenv('CYLC_CONTROL') == 'True'

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

    logger.debug('omnium import: {}'.format(import_log_msg))
    logger.debug(argv)
    logger.debug(args.cmd_name)
    logger.debug('cylc_control: {}'.format(cylc_control))

    cmd = omnium_cmds[args.cmd_name]
    if not args.throw_exceptions:
        logger.debug('Catching all exceptions')
        try:
            # dispatch on arg
            return cmd.main(args)
        except Exception as e:
            logger.error('{}'.format(e))
            return 1
    else:
        return cmd.main(args)
