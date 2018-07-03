"""Activates tests bundled with omnium or runs tests for analysis"""
import importlib
import os
from logging import getLogger
import subprocess as sp

logger = getLogger('om.test')

ARGS = [(['--analysis', '-a'], {'help': 'analysis to test'}),
        (['--all'], {'help': 'Run all tests', 'action': 'store_true'})]
RUN_OUTSIDE_SUITE = True


def run_omnium_tests():
    logger.info('Running omnium tests')
    omnium_home = os.path.dirname(os.path.realpath(os.path.join(__file__, '..')))
    logger.debug(omnium_home)
    os.chdir(os.path.join(omnium_home, 'tests'))
    logger.debug(os.getcwd())
    # Why not use:
    # nose.run(argv=['nosetests'])
    # it seems to do funny things to stdout.
    sp.check_output(['nosetests'])


def run_analysis_tests(analysis):
    logger.info('Running tests for analysis: {}', analysis)
    pkg = importlib.import_module(analysis)
    pkg_dir = os.path.dirname(pkg.__file__)
    tests_dir = os.path.join(pkg_dir, 'tests')
    if not os.path.exists(tests_dir):
        logger.info('Tests dir {} does not exist', tests_dir)
        return
    os.chdir(tests_dir)
    logger.debug(os.getcwd())
    sp.check_output(['nosetests'])


def main(suite, args):
    if not args.analysis or args.all:
        run_omnium_tests()

    if args.all:
        analysis_pkgs = os.environ.get('OMNIUM_ANALYSER_PKGS').split(':')
        logger.info('Found analysis packages: {}', ', '.join(analysis_pkgs))
        for analysis_pkg in analysis_pkgs:
            run_analysis_tests(analysis_pkg)

    elif args.analysis:
        run_analysis_tests(args.analysis)
