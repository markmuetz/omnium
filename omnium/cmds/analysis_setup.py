"""Clones an omnium analysis pkg"""
import os
import subprocess as sp
from logging import getLogger

from omnium.omnium_errors import OmniumError

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

        local = analysis_pkg_config.getboolean('local', False)
        repo = analysis_pkg_config['repo']
        reponame = analysis_pkg_config['reponame']
        commit = analysis_pkg_config['commit']

        if local:
            logger.info('Using local package')
            assert os.path.exists(repo)

            if os.path.exists(reponame):
                if os.path.islink(reponame):
                    logger.debug('local symlink already exists')
                else:
                    raise OmniumError('Reponame {} already exists in {} and is not a symlink\n'
                                      'Try removing directory manually'
                                      .format(reponame, os.getcwd()))
            else:
                logger.info('Creating symlink {}', reponame)
                os.symlink(repo, reponame)
            continue

        if os.path.exists(repo):
            raise OmniumError('repo {} is a local path: use the local=True setting'.format(repo))

        logger.info('  analysis_pkg repo: {}', repo)
        logger.info('  analysis_pkg reponame: {}', reponame)
        logger.info('  analysis_pkg commit: {}', commit)
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
