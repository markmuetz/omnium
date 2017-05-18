"""Syncs a mirror with a data source"""
import os
from logging import getLogger

logger = getLogger('omnium')

ARGS = [(['--host'], {'help': 'mmuetz@login.archer.ac.uk', 'default': 'mmuetz@login.archer.ac.uk'}),
        (['--suite', '-s'], {'help': 'u-AAXXX', 'default': 'u-al000'})]


def main(args):
    import subprocess as sp
    from omnium.suite import Suite
    suite = Suite()
    try:
        suite.check_in_suite_dir(os.getcwd())
    except OmniumError:
        pass
    
    if suite.is_in_suite:
        logger.info('Calling from suite {}'.format(suite.name))
        suite_name = suite.name
    else:
        suite_name = args.suite

    includes = ['*/', '*.conf', '*.py', '*.sh', '*.info', 'suite*rc*', 'log*Z', 'log*.tar.gz']
    include = ' '.join(["--include '{}'".format(inc) for inc in includes])

    cmd_fmt = "rsync -zarv --progress {include} --exclude '*' --prune-empty-dirs {host}:work/cylc-run/{src_suite}/ {dst_suite}"
    if suite.is_in_suite:
        logger.debug('cd to {}'.format(suite.suite_dir))
        cwd = os.getcwd()
        os.chdir(suite.suite_dir)
        cmd = cmd_fmt.format(include=include, host=args.host, src_suite=suite_name, dst_suite='.')
    else:
        cmd = cmd_fmt.format(include=include, host=args.host, src_suite=suite_name, dst_suite=suite_name)

    logger.debug(cmd)
    sp.call(cmd, shell=True)

    if suite.is_in_suite:
        logger.debug('cd to {}'.format(cwd))
        os.chdir(cwd)
