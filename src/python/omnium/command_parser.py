import argparse


def parse_commands(name, args, module):
    # create the top-level parser.
    parser = argparse.ArgumentParser(prog=name)
    subparsers = parser.add_subparsers(dest='cmd_name')

    for args, kwargs in args:
        parser.add_argument(*args, **kwargs)

    cmds = {}
    for cmd_name in module.commands:
        # create the subparser for each command.
        cmd = getattr(module, cmd_name.replace('-', '_'))
        subparser = subparsers.add_parser(cmd_name, 
                                          help=cmd.__doc__)
        for args, kwargs in cmd.ARGS:
            subparser.add_argument(*args, **kwargs)
        cmds[cmd_name] = cmd
    
    args = parser.parse_args()

    return cmds, args


