import os
import sys
import imp

from command_parser import parse_commands
from check_config import ConfigChecker, ConfigError
from setup_logging import setup_logger

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

    # Args overrides settings.
    if args.DEBUG:
        config['settings']['console_log_level'] = 'debug'

    logger = setup_logger(config)
    logger.info('omni {}'.format(' '.join(sys.argv[1:])))

    if args.cmd_name != 'check-config':
        logger.info('checking config')
        checker = ConfigChecker(args, config)
        try:
            checker.run_checks()
            for warning in checker.warnings:
                logger.warn(warning)
        except ConfigError as e:
            logger.error('CONFIG ERROR: {}'.format(e.message))
            if e.hint:
                logger.error(e.hint)
            logger.error('To check all config errors run:\nomni check-config')
            exit(1)
        logger.info('config OK')

    if config['settings']['ignore_warnings']:
        # DO NOT LEAVE IN!!!
        # Added so as orography warning not shown on iris.load.
        # Orography warning gone, now get iris warning about FUTURE promoting.
        logger.warn('Disabling warnings')
        import warnings
        warnings.filterwarnings("ignore")

    # dispatch on arg
    cmd = cmds[args.cmd_name]
    logger.debug('running cmd: {}'.format(cmd))
    if not args.throw_exceptions:
        logger.debug('catching all exceptions')
        try:
            cmd.main(args, config)
        except Exception as e:
            logger.warn('ERROR: {}'.format(e))
            exit(1)
    else:
        cmd.main(args, config)
    exit(0)


if __name__ == '__main__':
    main()
