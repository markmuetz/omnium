import os
import subprocess as sp
from collections import namedtuple
from logging import getLogger

from omnium.utils import get_git_info

logger = getLogger('om.pkg_state')

CondaState = namedtuple('CondaState', ['name', 'version', 'build', 'channel'])
PipState = namedtuple('PipState', ['name', 'version', 'loc', 'editable'])


def _version_from_str(version_str):
    return tuple([int(s) for s in version_str.split('.')])


class PkgState:
    """Installation state of package

    Has info on: location, git_info, conda_info, pip_info
    """
    def __init__(self, pkg, full=False):
        self.pkg = pkg
        self.pkg_name = pkg.__name__
        self.location = self._get_location(pkg)
        self.git_info = get_git_info(self.location)
        self.full = full
        self.conda_info = None
        self.pip_info = None
        if self.full:
            self.conda_info = self._get_conda_installation_details(self.pkg_name)
            self.pip_info = self._get_pip_installation_details(self.pkg_name)

    def __repr__(self):
        return 'State({}, {})'.format(self.pkg.__name__, self.full)

    def __str__(self):
        fmt_str = '{}\n  loc: {}\n  git_info: {}\n  conda_info: {}\n  pip_info: {}\n '
        return fmt_str.format(repr(self),
                              self.location,
                              self.git_info,
                              self.conda_info,
                              self.pip_info)

    def _get_location(self, pkg):
        return os.path.dirname(os.path.realpath(pkg.__file__))

    def _get_conda_installation_details(self, pkg_name):
        try:
            cmd = 'conda list -f {}'.format(pkg_name)
            logger.debug(cmd)
            lines = sp.check_output(cmd.split()).decode().split('\n')
            conda_info = None
            for line in [l for l in lines if l and l[0] != '#']:
                split_line = line.split()
                if split_line[0] == pkg_name:
                    args = split_line
                    args[1] = _version_from_str(args[1])
                    if len(args) == 3:
                        args.append(None)
                    conda_info = CondaState(*split_line)
                    break
            return conda_info
        except:
            return None

    def _get_pip_installation_details(self, pkg_name):
        try:
            cmd = 'pip list'
            logger.debug(cmd)
            lines = sp.check_output(cmd.split()).decode().split('\n')
            pip_info = None
            for line in [l for l in lines if l and l[0] != '#']:
                split_line = line.split()
                if split_line[0] == pkg_name:
                    if len(split_line) == 3:
                        pip_info = PipState(split_line[0],
                                            _version_from_str(split_line[1]),
                                            split_line[2],
                                            True)
                    else:
                        pip_info = PipState(split_line[0],
                                            _version_from_str(split_line[1]),
                                            '',
                                            False)
                    break
            return pip_info
        except:
            return None
