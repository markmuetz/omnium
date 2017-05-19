import os
from collections import OrderedDict as odict
import subprocess as sp


class State(object):
    """State of the omnium project directory

    location, git_hash, git_status and conda_env.
    """
    def __init__(self):
        self.location = self._get_location()
        self.git_hash, self.git_status = self._get_git_info(self.location)
        self.conda_env = self._get_conda_env()

    def _get_location(self):
        return os.path.dirname(os.path.realpath(__file__))

    def _get_git_info(self, location):
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

    def _get_conda_env(self):
        return os.environ.get('CONDA_DEFAULT_ENV')
