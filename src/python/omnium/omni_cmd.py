import os

from command_parser import parse_commands
from configobj import ConfigObj
import omni_cmds


ARGS = [(['-c', '--config-file'], {'default': 'omni.conf'}),
        (['-x', '--throw-exceptions'], {'action': 'store_true', 'default': False}), 
        (['--DEBUG'], {'action': 'store_true', 'default': False})]


def main():
    cmds, args = parse_commands('omni', ARGS, omni_cmds)
    cwd = os.getcwd()
    args.cwd = cwd
    config = ConfigObj(args.config_file)

    if config['settings'].as_bool('ignore_warnings'):
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
        except Exception, e:
            print('ERROR: {}'.format(e.message))
            exit(1)
    else:
        cmd.main(args, config)
    exit(0)


if __name__ == '__main__':
    main()
