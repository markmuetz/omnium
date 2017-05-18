"""Provide an easy way of getting analyzer classes by name"""
import os
import sys
from glob import glob
from collections import OrderedDict
import inspect
import imp

from analyzer import Analyzer

def get_analysis_classes(cwd=None):
    print(cwd)
    # Discovery of analysis classes in a given directory.
    if not cwd:
        cwd = os.getcwd()
    modules = []
    local_python_path = os.path.join(cwd, 'analysis')

    # Load the modules.
    if os.path.exists(local_python_path):
        for filename in sorted(glob(os.path.join(local_python_path, '*.py'))):
	    print(filename)
            module_name = os.path.splitext(os.path.basename(filename))[0]
            module = imp.load_source(module_name, filename)
            modules.append(module)

    current_module = sys.modules[__name__]
    modules.append(current_module)

    # Find subclasses of Analyzer
    analysis_classes = OrderedDict()
    for module in modules:
        for name, obj in inspect.getmembers(module):
	    #print((name, obj))
            if inspect.isclass(obj) and issubclass(obj, Analyzer) and not obj == Analyzer:
                if obj.analysis_name:
		    print(obj.analysis_name)
                    analysis_classes[obj.analysis_name] = obj
    print(analysis_classes)
    return analysis_classes

#from surf_flux_analysis import SurfFluxAnalyzer
#from restart_dump_analysis import RestartDumpAnalyzer
#from profile_analysis import ProfileAnalyzer
#from cloud_analysis import CloudAnalyzer
#from mass_flux_analysis import MassFluxAnalyzer
#from mass_flux_spatial_scales_analysis import MassFluxSpatialScalesAnalyzer
#
#ANALYZERS = {
#    SurfFluxAnalyzer.analysis_name: SurfFluxAnalyzer,
#    RestartDumpAnalyzer.analysis_name: RestartDumpAnalyzer,
#    ProfileAnalyzer.analysis_name: ProfileAnalyzer,
#    CloudAnalyzer.analysis_name: CloudAnalyzer,
#    MassFluxAnalyzer.analysis_name: MassFluxAnalyzer,
#    MassFluxSpatialScalesAnalyzer.analysis_name: MassFluxSpatialScalesAnalyzer,
#}
