import os
from collections import OrderedDict as odict

from utils import get_git_info


class State(object):
    """State of the omnium project directory

    location, git_hash, git_status and conda_env.
    """
    def __init__(self):
        self.location = self._get_location()
        self.git_hash, self.git_status = get_git_info(self.location)
        self.conda_env = self._get_conda_env()

    def _get_location(self):
        return os.path.dirname(os.path.realpath(__file__))

    def _get_conda_env(self):
        return os.environ.get('CONDA_DEFAULT_ENV')
