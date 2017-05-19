import sys

from command_parser import parse_commands
from setup_logging import setup_logger
import cmds


ARGS = [(['-x', '--throw-exceptions'], {'action': 'store_true', 'default': False}),
        (['--DEBUG'], {'action': 'store_true', 'default': False})]


def main(argv):
    omnium_cmds, args = parse_commands('omnium', ARGS, cmds, argv[1:])
    if args.DEBUG:
        logger = setup_logger(True)
    else:
        logger = setup_logger()
    logger.debug(argv)
    logger.debug(args.cmd_name)
    cmd = omnium_cmds[args.cmd_name]
    if not args.throw_exceptions:
        logger.debug('catching all exceptions')
        try:
            # dispatch on arg
            return cmd.main(args)
        except Exception as e:
            logger.error('{}'.format(e))
            return 1
    else:
        return cmd.main(args)
