"""Syncs a mirror with a data source"""
import os
from logging import getLogger

from omnium.omnium_errors import OmniumError

logger = getLogger('omnium')

ARGS = [(['--host'], {'help': 'mmuetz@login.archer.ac.uk', 'default': 'mmuetz@login.archer.ac.uk'}),
        (['--create', '-c'], {'help': 'u-AAXXX'}),
        (['--verbose', '-v'], {'help': 'Set verbose on for rsync', 'action': 'store_true'}),
        # TODO: Not properly working with multiple args.
        (['--rsync-args'], {'help': 'Additional rsync args (e.g. --rsync-args="--update"', 'default': ''}),
        (['exts'], {'help': 'Additional extensions to include (e.g. .png .pp1.nc)', 'nargs': '*'})]


def main(args):
    import subprocess as sp
    from omnium.suite import Suite
    suite = Suite()
    try:
        suite.check_in_suite_dir(os.getcwd())
    except OmniumError:
        pass
    
    if suite.is_in_suite:
        if args.create:
            logger.error('Cannot use --create from within a suite')
            return 1
        logger.info("Sync'ing suite mirror: {}".format(suite.name))
        suite_name = suite.name
    else:
        if not args.create:
            logger.error('Must be called from within a suite or with --create')
            return 1
        else:
            suite_name = args.create
            if os.path.exists(suite_name):
                logger.error('Mirror {} already exists'.format(suite_name))
                return 1
            logger.info('Creating suite mirror: {}'.format(suite.name))

    # First include is necessary to make sure all dirs are included?
    # Gets configuration, python, shell scripts, info, cylc suite, and logs by default.
    includes = ['*/', '*.conf', '*.py', '*.sh', '*.info', 'suite*rc*', 'log*Z', 'log*.tar.gz']
    # Extend with any exts passed by user.
    includes.extend(['*' + ext for ext in args.exts])
    include = ' '.join(["--include '{}'".format(inc) for inc in includes])

    verbose = 'v' if args.verbose else ''
    progress = '--progress' if args.verbose else ''
    # --exclude makes sure that only the filetypes asked for are downloaded.
    cmd_fmt = "rsync -zar{verbose} {progress} {rsync_args} {include} --exclude '*' --prune-empty-dirs {host}:work/cylc-run/{src_suite}/ {dst_suite}"

    if suite.is_in_suite:
        logger.debug('cd to {}'.format(suite.suite_dir))
        cwd = os.getcwd()
        os.chdir(suite.suite_dir)
        dst_suite = '.'
    else:
        dst_suite = suite_name

    cmd = cmd_fmt.format(verbose=verbose, 
                         progress=progress, 
                         rsync_args=args.rsync_args, 
                         include=include, 
                         host=args.host, 
                         src_suite=suite_name, 
                         dst_suite=suite_name)

    logger.debug(cmd)
    sp.call(cmd, shell=True)

    if suite.is_in_suite:
        logger.debug('cd back to {}'.format(cwd))
        os.chdir(cwd)
        logger.info("Sync'd")
    else:
        logger.info('Created')
        # TODO: create <suite>/.omnium/suite.conf etc.
