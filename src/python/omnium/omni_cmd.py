import os
import sys

from command_parser import parse_commands
from check_config import ConfigChecker, ConfigError
import imp

import omni_cmds


ARGS = [(['-c', '--config-file'], {'default': 'omni_conf.py'}),
        (['-x', '--throw-exceptions'], {'action': 'store_true', 'default': False}), 
        (['--DEBUG'], {'action': 'store_true', 'default': False})]


def main():
    cmds, args = parse_commands('omni', ARGS, omni_cmds)
    cwd = os.getcwd()
    args.cwd = cwd
    config_path = os.path.join(cwd, args.config_file)

    # Stops .pyc file from being created.
    sys.dont_write_bytecode = True
    config_module = imp.load_source('omni_conf', config_path)
    sys.dont_write_bytecode = False

    settings = [d for d in dir(config_module) if d[:2] not in ['__']]
    config = dict((s, getattr(config_module, s)) for s in settings)

    if args.cmd_name != 'check-config':
        checker = ConfigChecker(args, config)
        try:
            checker.run_checks()
        except ConfigError as e:
            print('CONFIG ERROR: {}'.format(e.message))
            print(e.hint)
            print('To check all config errors run:\nomni check-config')
            exit(1)

    if config['settings']['ignore_warnings']:
        # DO NOT LEAVE IN!!!
        # Added so as orography warning not shown on iris.load.
        # Orography warning gone, now get iris warning about FUTURE promoting.
        print('Disabling warnings')
        import warnings
        warnings.filterwarnings("ignore")

    # dispatch on arg
    cmd = cmds[args.cmd_name]
    if not args.throw_exceptions:
        try:
            cmd.main(args, config)
        except Exception as e:
            print('ERROR: {}'.format(e))
            exit(1)
    else:
        cmd.main(args, config)
    exit(0)


if __name__ == '__main__':
    main()
