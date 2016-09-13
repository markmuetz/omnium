
import os
from collections import OrderedDict as odict
import subprocess as sp


def _get_location():
    return os.path.dirname(os.path.realpath(__file__))


def _get_uncommitted_changes(location):
    cwd = os.getcwd()
    os.chdir(location)
    try:
        if sp.check_output('git status --porcelain'.split()) == '':
            return 'clean'
        else:
            return 'uncommitted_changes'
    except sp.CalledProcessError as ex:
        return 'not_git_repo'
    finally:
        os.chdir(cwd)


def _get_conda_env():
    return os.environ.get('CONDA_DEFAULT_ENV')


def get_omnium_state():
    location = _get_location()
    uncommitted_changes = _get_uncommitted_changes(location)
    conda_env = _get_conda_env()

    return odict([('location', location),
                  ('uncommitted_changes', uncommitted_changes),
                  ('conda_env', conda_env)])

