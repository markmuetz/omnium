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
        analysis_pkg_config = cmd_ctx.suite.app_config['analysis_{}'.format(analysis_pkg_name)]
        repo = analysis_pkg_config['repo']
        reponame = analysis_pkg_config['reponame']
        commit = analysis_pkg_config['commit']

        cwd = os.getcwd()

        if os.path.exists(reponame):
            os.chdir(reponame)
            cmd = 'git pull'
            sp.call(cmd, shell=True)
        else:
            cmd = 'git clone {} {}'.format(repo, reponame)
            sp.call(cmd, shell=True)
            os.chdir(reponame)

        cmd = 'git checkout {}'.format(commit)
        sp.call(cmd, shell=True)

        os.chdir(cwd)
    os.chdir(orig_cwd)
