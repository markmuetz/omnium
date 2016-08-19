from command_parser import parse_commands
import omnium_cmds

ARGS = []

def main():
    cmds, args = parse_commands('omnium', ARGS, omnium_cmds)
    # dispatch on arg
    cmd = cmds[args.cmd_name]
    cmd.main(args)


if __name__ == '__main__':
    main()
