import os
from collections import OrderedDict as odict
import subprocess as sp


def _get_location():
    return os.path.dirname(os.path.realpath(__file__))


def _get_git_info(location):
    cwd = os.getcwd()
    os.chdir(location)
    try:
        git_hash = sp.check_output('git rev-parse HEAD'.split()).strip()
        if sp.check_output('git status --porcelain'.split()) == '':
            return git_hash, 'clean'
        else:
            return git_hash, 'uncommitted_changes'
    except sp.CalledProcessError as ex:
        return None, 'not_git_repo'
    finally:
        os.chdir(cwd)


def _get_conda_env():
    return os.environ.get('CONDA_DEFAULT_ENV')


def get_omnium_state():
    location = _get_location()
    git_hash, uncommitted_changes = _get_git_info(location)
    conda_env = _get_conda_env()

    return odict([('location', location),
                  ('git_hash', git_hash),
                  ('uncommitted_changes', uncommitted_changes),
                  ('conda_env', conda_env)])
