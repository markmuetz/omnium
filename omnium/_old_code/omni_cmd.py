import os
import sys

from version import get_version
from omnium_state import get_omnium_state
from command_parser import parse_commands
from check_config import ConfigChecker, ConfigError
from setup_logging import setup_logger
from processes import get_process_classes

import omni_cmds


ARGS = [(['-c', '--config-file'], {'default': 'omni_conf.py'}),
        (['-x', '--throw-exceptions'], {'action': 'store_true', 'default': False}),
        (['--DEBUG'], {'action': 'store_true', 'default': False})]


def main(argv):
    cmds, args = parse_commands('omni', ARGS, omni_cmds, argv[1:])

    cwd = os.getcwd()
    args.cwd = cwd
    config_path = os.path.join(cwd, args.config_file)
    config = ConfigChecker.load_config(config_path)

    # Args overrides settings.
    if args.DEBUG:
        config['settings']['console_log_level'] = 'debug'

    logger = setup_logger(config)
    logger.debug('omnium.__version__: {}'.format(get_version('long')))
    omnium_state = get_omnium_state()
    for key, value in omnium_state.items():
        logger.debug('state: {}: {}'.format(key, value))

    logger.debug('cmd: omni {}'.format(' '.join(sys.argv[1:])))

    process_classes = get_process_classes(cwd)
    if args.cmd_name != 'check-config':
        logger.debug('checking config')
        try:
            checker = ConfigChecker(config, process_classes)
            checker.run_checks()
            for warning in checker.warnings:
                logger.warn(warning)
        except ConfigError as e:
            logger.error('CONFIG ERROR: {}'.format(e.message))
            if e.hint:
                logger.error(e.hint)
            logger.error('To check all config errors run:\nomni check-config')
            return 1
        except Exception as e:
            logger.error('{}'.format(e))
            return 1
        logger.debug('config OK')

    if config['settings']['ignore_warnings']:
        # DO NOT LEAVE IN!!!
        # Added so as orography warning not shown on iris.load.
        # Orography warning gone, now get iris warning about FUTURE promoting.
        logger.warn('Disabling Python warnings')
        import warnings
        warnings.filterwarnings("ignore")

    # dispatch on arg
    cmd = cmds[args.cmd_name]
    logger.debug('running cmd: {}'.format(cmd))
    if not args.throw_exceptions:
        logger.debug('catching all exceptions')
        try:
            return cmd.main(args, config, process_classes)
        except Exception as e:
            logger.error('{}'.format(e))
            return 1
    else:
        cmd.main(args, config, process_classes)
    return 0
