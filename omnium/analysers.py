"""Provide an easy way of getting analyser classes by name"""
import imp
import inspect
import os
import sys
from collections import OrderedDict
from glob import glob
from logging import getLogger

from omnium.analyser import Analyser
from omnium.converter import FF2NC_Converter
from omnium.deleter import Deleter
from omnium.omnium_errors import OmniumError
from omnium.utils import get_git_info

logger = getLogger('om.analysers')


class Analysers(object):

    @staticmethod
    def get_analysis_classes(cwd=None):
        """Discovery of analysis classes in a given directory

        Searches in dir cwd/analysis for python files.
        Loads all python files and any subclasses of Analyser are returned in a dict."""
        logger.debug('loading analysers from: {}'.format(cwd))
        if not cwd:
            cwd = os.getcwd()
        modules = []
        local_python_path = os.path.join(cwd, 'analysis')

        # Load the modules.
        if os.path.exists(local_python_path):
            for filename in sorted(glob(os.path.join(local_python_path, '*.py'))):
                if os.path.basename(filename) in ['__init__.py']:
                    continue
                module_name = os.path.splitext(os.path.basename(filename))[0]
                module = imp.load_source(module_name, filename)
                modules.append(module)

        # Find subclasses of Analyser
        analysis_classes = OrderedDict()

        for module in modules:
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, Analyser) and not obj == Analyser:
                    if obj.analysis_name:
                        logger.debug('loading from: {}, {}'.format(cwd, obj.analysis_name))
                        if obj.analysis_name in analysis_classes:
                            msg = 'Analysis {} has already been added'.format(obj.analysis_name)
                            raise OmniumError(msg)
                        analysis_classes[obj.analysis_name] = obj
        return analysis_classes

    def __init__(self, analyser_dirs):
        self.analyser_dirs = analyser_dirs
        self.analysis_classes = OrderedDict()
        self.analysis_hash = []
        self.analysis_status = []
        self.analysis_groups = OrderedDict()

    def find_all(self):
        if self.analyser_dirs:
            # First dir takes precedence over second etc.
            for analyser_dir in self.analyser_dirs:
                analyser_dir = analyser_dir.rstrip('/')
                if not os.path.exists(analyser_dir):
                    logger.warning('Analysers dir does not exists: {}'.format(analyser_dir))
                else:
                    logger.debug('loading analyser dir: {}'.format(analyser_dir))
                    sys.path.append(analyser_dir)

                    git_hash, git_status = get_git_info(analyser_dir)
                    logger.debug('analysers git_hash, status: {}, {}'.format(git_hash, git_status))
                    analysis_classes = Analysers.get_analysis_classes(analyser_dir)
                    self.analysis_hash.append(git_hash)
                    self.analysis_status.append(git_status)
                    # Add any analysers *not already in classes*.
                    for k, v in analysis_classes.items():
                        if k not in self.analysis_classes:
                            self.analysis_classes[k] = v
                            self.analysis_groups[k] = os.path.basename(analyser_dir)
                        else:
                            logger.warning('Multiple analysis classes named: {}'.format(k))

        self.analysis_classes[FF2NC_Converter.analysis_name] = FF2NC_Converter
        self.analysis_groups[FF2NC_Converter.analysis_name] = 'omnium'
        self.analysis_classes[Deleter.analysis_name] = Deleter
        self.analysis_groups[Deleter.analysis_name] = 'omnium'
