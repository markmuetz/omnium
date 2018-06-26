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
    def __init__(self, analyser_packages):
        self.analyser_packages = analyser_packages
        self.analysis_packages_settings = {}
        self.analysis_classes = OrderedDict()
        self.analysis_hash = []
        self.analysis_status = []
        self.analysis_groups = OrderedDict()
        self.have_found = False

    def find_all(self):
        if self.have_found:
            raise OmniumError('Should only call find_all once')

        if self.analyser_packages:
            # First dir takes precedence over second etc.
            for analyser_package in self.analyser_packages:
                try:
                    pkg = importlib.import_module(analyser_package)
                except ImportError:
                    logger.error("Package '{}' not found on PYTHONPATH", analyser_package)

                self.analysis_packages_settings[analyser_package] = pkg.analysis_settings
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
                    self.analyser_packages
                    if cls not in self.analysis_classes:
                        self.analysis_classes[cls.analysis_name] = cls
                        self.analysis_groups[cls.analysis_name] = \
                            os.path.basename(analyser_package)
                    else:
                        logger.warning('Multiple analysis classes named: {}', cls)

        self.analysis_classes[FF2NC_Converter.analysis_name] = FF2NC_Converter
        self.analysis_groups[FF2NC_Converter.analysis_name] = 'omnium'

        self.analysis_classes[Deleter.analysis_name] = Deleter
        self.analysis_groups[Deleter.analysis_name] = 'omnium'
        self.have_found = True
