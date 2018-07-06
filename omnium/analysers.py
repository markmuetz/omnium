"""Provide an easy way of getting analyser classes by name"""
import importlib
import os
from collections import OrderedDict
from logging import getLogger

from omnium.converter import FF2NC_Converter
from omnium.deleter import Deleter
from omnium.omnium_errors import OmniumError
from omnium.utils import get_git_info

logger = getLogger('om.analysers')


class Analysers(object):
    def __init__(self, analyser_package_names):
        self.analyser_package_names = analyser_package_names
        self.analysis_packages = {}
        self.analysis_classes = OrderedDict()
        self.analysis_hash = []
        self.analysis_status = []
        self.analysis_groups = OrderedDict()
        self.have_found = False

        self._cls_to_pkg = {}

    def find_all(self):
        if self.have_found:
            raise OmniumError('Should only call find_all once')

        if self.analyser_package_names:
            # First dir takes precedence over second etc.
            for analyser_package_name in self.analyser_package_names:
                try:
                    pkg = importlib.import_module(analyser_package_name)
                except ImportError:
                    logger.error("Package '{}' not found on PYTHONPATH", analyser_package_name)
                    continue

                self.analysis_packages[analyser_package_name] = pkg
                pkg_dir = os.path.dirname(pkg.__file__)
                try:
                    pkg_hash, pkg_status = get_git_info(pkg_dir)
                    self.analysis_hash.append(pkg_hash)
                    self.analysis_status.append(pkg_status)
                except:
                    logger.warning('analysis pkg is not a git repo: {}', pkg_dir)
                    self.analysis_hash.append('')
                    self.analysis_status.append('not_a_git_repo')

                for cls in pkg.analysis_classes:
                    if cls not in self.analysis_classes:
                        self._cls_to_pkg[cls] = analyser_package_name
                        self.analysis_classes[cls.analysis_name] = cls
                        self.analysis_groups[cls.analysis_name] = \
                            os.path.basename(analyser_package_name)
                    else:
                        logger.warning('Multiple analysis classes named: {}', cls)

        self.have_found = True

    def get_settings(self, analyser_cls, settings_name):
        logger.debug('getting settings for {}', analyser_cls)
        analyser_package_name = self._cls_to_pkg[analyser_cls]
        package = self.analysis_packages[analyser_package_name]
        logger.debug('{} in package {}', analyser_cls, package)
        settings_dict = package.analysis_settings
        if settings_name not in settings_dict:
            raise OmniumError('Settings {} not defined in {}, choices are {}'
                              .format(settings_name, analyser_package_name, settings_dict.keys()))
        return package.analysis_settings_filename, settings_dict[settings_name]

    def get_package(self, analyser_cls):
        analyser_package_name = self._cls_to_pkg[analyser_cls]
        package = self.analysis_packages[analyser_package_name]
        return package
