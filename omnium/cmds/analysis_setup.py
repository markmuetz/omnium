"""Clones an omnium analysis pkg"""
import os
import subprocess as sp
from logging import getLogger

logger = getLogger('om.analysis_setup')

ARGS = []


def main(cmd_ctx, args):
    orig_cwd = os.getcwd()
    os.chdir(os.path.join(cmd_ctx.suite.suite_dir, '.omnium'))
    os.makedirs('analysis_pkgs', exist_ok=True)
    os.chdir('analysis_pkgs')

    analysis_pkgs = cmd_ctx.suite.app_config.get('env', 'OMNIUM_ANALYSIS_PKGS')
    analysis_pkg_names = analysis_pkgs.split(':')

    for analysis_pkg_name in analysis_pkg_names:
        logger.info('Setting up analysis_pkg: {}', analysis_pkg_name)
        analysis_pkg_config = cmd_ctx.suite.app_config['analysis_{}'.format(analysis_pkg_name)]
        repo = analysis_pkg_config['repo']
        reponame = analysis_pkg_config['reponame']
        commit = analysis_pkg_config['commit']
        logger.info('  analysis_pkg repo: {}', repo)
        logger.info('  analysis_pkg reponame: {}', reponame)
        logger.info('  analysis_pkg commit: {}', reponame)
        cwd = os.getcwd()

        if os.path.exists(reponame):
            logger.debug('repo exists: pulling')
            os.chdir(reponame)
            cmd = 'git pull'
            sp.call(cmd, shell=True)
        else:
            logger.debug('repo does not exist: cloning')
            cmd = 'git clone {} {}'.format(repo, reponame)
            sp.call(cmd, shell=True)
            os.chdir(reponame)

        cmd = 'git checkout {}'.format(commit)
        logger.debug('checking out {}', commit)
        sp.call(cmd, shell=True)

        os.chdir(cwd)
    os.chdir(orig_cwd)
