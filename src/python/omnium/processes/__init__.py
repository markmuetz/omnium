import os
import sys
from glob import glob
from collections import OrderedDict
import inspect
import importlib

from processes import Process
from iris_processes import (ConvertPpToNc, ConvertMassToEnergyFlux,
                            TimeDelta, DomainMean)
from pylab_processes import PlotMultiTimeseries, PlotLastProfile


def _get_process_classes(cwd=None):
    if not cwd:
        cwd = os.getcwd()
    modules = []
    local_python_path = os.path.join(cwd, 'src/python')
    if os.path.exists(local_python_path):
        sys.path.insert(0, local_python_path)
        for filename in glob(os.path.join(local_python_path, '*')):
            module_name = os.path.splitext(os.path.basename(filename))[0]
            module = importlib.import_module(module_name)
            modules.append(module)
        sys.path.remove(local_python_path)

    current_module = sys.modules[__name__]
    modules.append(current_module)

    process_classes = OrderedDict()
    for module in modules:
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and\
               issubclass(obj, Process) and\
               not obj == Process:
                process_classes[obj.name] = obj
    return process_classes

process_classes = _get_process_classes()


def proc_instance(config, node):
    assert(node.process)
    return process_classes[node.process](config, node)
