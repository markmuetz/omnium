import importlib
import os
import sys
from logging import getLogger
from typing import List

from omnium.omnium_errors import OmniumError
from omnium.pkg_state import PkgState
from omnium.version import get_version
from omnium.suite import Suite
from omnium.utils import check_git_commits_equal, cd
from .analyser import Analyser

logger = getLogger('om.analysis_pkg')


class AnalysisPkg(dict):
    """Wrapper around an analysis package.

    An analysis package is a python package that has certain variables.

    It must have in its top level:
    __version__: Tuple[int]
    analyser_classes: List[Analyser]
    analysis_settings_filename: str - where settings.json will get written to
    analysis_settings = Dict[str, AnalysisSettings]
    """
    def __init__(self, name: str, pkg, suite: Suite):
        self.name = name
        self.pkg = pkg
        self.suite = suite
        self.state = PkgState(self.pkg)
        self.version = self.pkg.__version__
        self.pkg_dir = os.path.dirname(self.pkg.__file__)

        for cls in pkg.analyser_classes:
            if cls not in self:
                self[cls.analysis_name] = cls
            else:
                logger.warning('Multiple analysis classes named: {}', cls)

        self.analysis_settings = self.pkg.analysis_settings
        self.analysis_settings_filename = self.pkg.analysis_settings_filename

        analysis_pkg_config = self.suite.app_config['analysis_{}'.format(self.name)]
        commit = analysis_pkg_config['commit']

        with cd(self.pkg_dir):
            if not check_git_commits_equal('HEAD', commit):
                msg = 'analysis_pkg {} not at correct version'.format(self.name)
                logger.error(msg)
                logger.error('try running `omnium analysis-setup` to fix')
                raise OmniumError(msg)


class AnalysisPkgs(dict):
    """Contains all analysis packages"""
    def __init__(self, analysis_pkg_names: List[str], suite: Suite):
        self._analysis_pkg_names = analysis_pkg_names
        self.suite = suite
        self._cls_to_pkg = {}
        self.analyser_classes = {}
        self.have_found = False
        if self.suite.is_in_suite:
            self._load()

    def _load(self):
        if self.have_found:
            raise OmniumError('Should only call load once')

        analysis_pkgs_dir = os.path.join(self.suite.suite_dir, '.omnium/analysis_pkgs')
        if not os.path.exists(analysis_pkgs_dir):
            logger.warning('analysis_pkg_dir: {} does not exist', analysis_pkgs_dir)
            return
        for analysis_pkg_dir in os.listdir(analysis_pkgs_dir):
            sys.path.append(os.path.join(analysis_pkgs_dir, analysis_pkg_dir))

        if self._analysis_pkg_names:
            # First dir takes precedence over second etc.
            for analyser_pkg_name in self._analysis_pkg_names:
                try:
                    pkg = importlib.import_module(analyser_pkg_name)
                except ImportError as e:
                    logger.error("Package '{}' not found on PYTHONPATH", analyser_pkg_name)
                    logger.error("Or could not load it")
                    logger.error(e)
                    continue
                analysis_pkg = AnalysisPkg(analyser_pkg_name, pkg, self.suite)

                for cls_name, cls in analysis_pkg.items():
                    self._cls_to_pkg[cls] = analysis_pkg
                    self.analyser_classes[cls_name] = cls

                self[analyser_pkg_name] = analysis_pkg
        self.have_found = True

    def get_settings(self, analyser_cls, settings_name):
        analysis_pkg = self._cls_to_pkg[analyser_cls]
        logger.debug('analysis_cls {} in package {}', analyser_cls, analysis_pkg.name)
        settings_dict = analysis_pkg.analysis_settings
        if settings_name not in settings_dict:
            raise OmniumError('Settings {} not defined in {}, choices are {}'
                              .format(settings_name, analysis_pkg, settings_dict.keys()))
        return analysis_pkg.analysis_settings_filename, settings_dict[settings_name]

    def get_package(self, analyser_cls: Analyser) -> AnalysisPkg:
        return self._cls_to_pkg[analyser_cls]

    def get_package_version(self, analyser_cls):
        analysis_pkg = self._cls_to_pkg[analyser_cls]
        return AnalysisPkgs._get_package_version(analysis_pkg)

    @staticmethod
    def _get_package_version(package):
        return package.pkg.__name__ + '_v' + get_version(package.pkg.__version__, form='medium')
