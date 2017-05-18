import sys
from command_parser import parse_commands
import cmds

ARGS = []


def main(argv):
    omnium_cmds, args = parse_commands('omnium', ARGS, cmds, argv[1:])
    # dispatch on arg
    cmd = omnium_cmds[args.cmd_name]
    cmd.main(args)
    return 0
