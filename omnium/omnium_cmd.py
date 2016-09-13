import sys
from command_parser import parse_commands
import omnium_cmds

ARGS = []


def main(argv):
    cmds, args = parse_commands('omnium', ARGS, omnium_cmds, argv[1:])
    # dispatch on arg
    cmd = cmds[args.cmd_name]
    cmd.main(args)
    return 0
