import os
import sys
from glob import glob
from collections import OrderedDict
import inspect
import imp

from processes import Process
from iris_processes import (IrisProcess, ConvertPpToNc, ConvertMassToEnergyFlux,
                            TimeDelta, DomainMean)
from pylab_processes import PylabProcess, PlotMultiTimeseries, PlotLastProfile


# Gets called twice (if a src/python/mod1.py is def'd).
def get_process_classes(cwd=None):
    if not cwd:
        cwd = os.getcwd()
    modules = []
    local_python_path = os.path.join(cwd, 'src/python')
    if os.path.exists(local_python_path):
        for filename in glob(os.path.join(local_python_path, '*.py')):
            module_name = os.path.splitext(os.path.basename(filename))[0]
            module = imp.load_source(module_name, filename)
            modules.append(module)

    current_module = sys.modules[__name__]
    modules.append(current_module)

    process_classes = OrderedDict()
    for module in modules:
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and\
               issubclass(obj, Process) and\
               not obj == Process:
                if obj.name:
                    process_classes[obj.name] = obj
    return process_classes
