import argparse


def parse_commands(name, args, module):
    # create the top-level parser.
    parser = argparse.ArgumentParser(prog=name)
    subparsers = parser.add_subparsers(dest='cmd_name')

    for args, kwargs in args:
        parser.add_argument(*args, **kwargs)

    cmds = module.modules
    for cmd_name, cmd_module in cmds.items():
        # create the subparser for each command.
        #cmd = getattr(module, cmd_name.replace('-', '_'))
        subparser = subparsers.add_parser(cmd_name, 
                                          help=cmd_module.__doc__)
        for args, kwargs in cmd_module.ARGS:
            subparser.add_argument(*args, **kwargs)
        #cmds[cmd_name] = cmd
    
    args = parser.parse_args()

    return cmds, args


