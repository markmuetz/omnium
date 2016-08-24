import os
import sys
from glob import glob
from collections import OrderedDict
import inspect
import importlib

import iris

class Process(object):
    name = None


class DomainMean(Process):
    name = 'domain_mean'
    out_ext = 'nc'

    def run(self, to_node):
        print('running domain mean')

        results = []
        for from_node in to_node.from_nodes:
            cubes = iris.load(from_node.filename)
            for cube in cubes:
                cube_stash = cube.attributes['STASH']
                section, item = cube_stash.section, cube_stash.item
                if section == to_node.section and item == to_node.item:
                    break
            result = cube.collapsed(['grid_latitude', 'grid_longitude'], 
                                    iris.analysis.MEAN)
            results.append(result)

        results_cube = iris.cube.CubeList(results).concatenate_cube()
        iris.save(results_cube, to_node.filename)

        with open(to_node.filename + '.done', 'w') as f:
            f.write('{}\n'.format(results_cube))


class ConvertPpToNc(Process):
    name = 'convert_pp_to_nc'
    out_ext = 'nc'

    def run(self, to_node):
        print('Running convert')

        assert(len(to_node.from_nodes) == 1)
        from_node = to_node.from_nodes[0]

        print('Convert {} to {}'.format(from_node, to_node))
        cubes = iris.load(from_node.filename)
        if not len(cubes):
            print('Cubes is empty')
            return
        iris.save(cubes, to_node.filename)

        with open(to_node.filename + '.done', 'w') as f:
            f.write('{}'.format(cubes))


def get_process_classes(cwd):
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
            if (inspect.isclass(obj) and 
                issubclass(obj, Process) and
                not obj == Process):
                    process_classes[obj.name] = obj
    return process_classes
