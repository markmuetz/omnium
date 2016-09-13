import argparse
import argcomplete


def parse_commands(name, args, module, cmdline_args):
    # create the top-level parser.
    parser = argparse.ArgumentParser(prog=name)
    subparsers = parser.add_subparsers(dest='cmd_name')

    for args, kwargs in args:
        parser.add_argument(*args, **kwargs)

    cmds = module.modules
    for cmd_name, cmd_module in cmds.items():
        # create the subparser for each command.
        subparser = subparsers.add_parser(cmd_name,
                                          help=cmd_module.__doc__)
        for args, kwargs in cmd_module.ARGS:
            subparser.add_argument(*args, **kwargs)

    argcomplete.autocomplete(parser)
    args = parser.parse_args(cmdline_args)

    return cmds, args
