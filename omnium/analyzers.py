"""Provide an easy way of getting analyzer classes by name"""
import os
import sys
from glob import glob
from collections import OrderedDict
import inspect
import imp
from logging import getLogger

import omnium
from omnium.analyzer import Analyzer

logger = getLogger('omnium')


def get_analysis_classes(cwd=None):
    """Discovery of analysis classes in a given directory

    Searches in dir cwd/analysis for python files.
    Loads all python files and any subclasses of Analyzer are returned in a dict."""
    logger.debug('loading analyzers from: {}'.format(cwd))
    if not cwd:
        cwd = os.getcwd()
    modules = []
    local_python_path = os.path.join(cwd, 'analysis')

    # Load the modules.
    if os.path.exists(local_python_path):
        for filename in sorted(glob(os.path.join(local_python_path, '*.py'))):
            module_name = os.path.splitext(os.path.basename(filename))[0]
            module = imp.load_source(module_name, filename)
            modules.append(module)

    current_module = sys.modules[__name__]
    modules.append(current_module)

    # Find subclasses of Analyzer
    analysis_classes = OrderedDict()
    for module in modules:
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, Analyzer) and not obj == Analyzer:
                if obj.analysis_name:
                    logger.debug('loading from: {}, {}'.format(cwd, obj.analysis_name))
                    analysis_classes[obj.analysis_name] = obj
    return analysis_classes
