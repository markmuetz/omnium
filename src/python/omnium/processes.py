import os
import sys
from glob import glob
from collections import OrderedDict
import inspect
import importlib

import iris
import pylab as plt

class Process(object):
    name = None
    def __init__(self, args, config, computer_name):
        self.args = args
        self.config = config
        self.computer_name = computer_name

        if self.name in self.config['process_options']:
            self.options = self.config['process_options'][self.name]
        else:
            self.options = {}


class DomainMean(Process):
    name = 'domain_mean'
    out_ext = 'nc'

    def run(self, to_node):
        print('running domain mean')

        results = []
        for from_node in to_node.from_nodes:
            filename = from_node.filename(self.computer_name, self.config)
            print(filename)
            cubes = iris.load(filename)
            for cube in cubes:
                cube_stash = cube.attributes['STASH']
                section, item = cube_stash.section, cube_stash.item
                if section == to_node.section and item == to_node.item:
                    break
            result = cube.collapsed(['grid_latitude', 'grid_longitude'], 
                                    iris.analysis.MEAN)
            results.append(result)

        results_cube = iris.cube.CubeList(results).concatenate_cube()
        iris.save(results_cube, to_node.filename(self.computer_name, self.config))

        with open(to_node.filename(self.computer_name, self.config) + '.done', 'w') as f:
            f.write('{}\n'.format(results_cube))


class ConvertPpToNc(Process):
    name = 'convert_pp_to_nc'
    out_ext = 'nc'

    def run(self, to_node):
        print('Running convert')

        assert(len(to_node.from_nodes) == 1)
        from_node = to_node.from_nodes[0]

        print('Convert {} to {}'.format(from_node, to_node))
        cubes = iris.load(from_node.filename(self.computer_name, self.config))
        if not len(cubes):
            print('Cubes is empty')
            return
        iris.save(cubes, to_node.filename(self.computer_name, self.config))

        with open(to_node.filename(self.computer_name, self.config) + '.done', 'w') as f:
            f.write('{}'.format(cubes))


class PlotMultiTimeseries(Process):
    name = 'plot_multi_timeseries'
    out_ext = 'png'

    def run(self, node):
        print('Plotting timeseries')

        f, axes = plt.subplots(1, len(node.from_nodes))
        if len(node.from_nodes) == 1:
            axes = [axes]
        f.canvas.set_window_title('timeseries') 
        for i, from_node in enumerate(node.from_nodes):
            timeseries = iris.load(from_node.filename(self.computer_name, self.config))[0]

            times = timeseries.coords()[0].points.copy()
            times -= times[0]

            axes[i].plot(times / 24, timeseries.data)
            axes[i].set_xlabel('time (days)')
            axes[i].set_ylabel(timeseries.units)
            axes[i].set_title(timeseries.name())

        plt.savefig(node.filename(self.computer_name, self.config))
        with open(node.filename(self.computer_name, self.config) + '.done', 'w') as f:
            f.write('')


class PlotLastProfile(Process):
    name = 'plot_last_profile'
    out_ext = 'png'

    def run(self, node):
        print('Plotting profile')

        fig = plt.figure()
        fig.canvas.set_window_title('profile') 
        for i, from_node in enumerate(node.from_nodes):
            profile = iris.load(from_node.filename(self.computer_name, self.config))[0][0]
            plt.plot(profile.data, profile.coord('level_height').points, label=profile.name())

        plt.legend()

        plt.savefig(node.filename(self.computer_name, self.config))
        with open(node.filename(self.computer_name, self.config) + '.done', 'w') as f:
            f.write('')


class ConvertMassToEnergyFlux(Process):
    name = 'convert_mass_to_energy_flux'
    out_ext = 'nc'

    def run(self, to_node):
        assert(len(to_node.from_nodes) == 1)
        from_node = to_node.from_nodes[0]

        print('Convert {} to {}'.format(from_node, to_node))
        precip = iris.load(from_node.filename(self.computer_name, self.config))[0]

	print(precip.shape)
        L = iris.cube.Cube(2.5e6, long_name='latent_heat_of_evap', units='J kg-1')
	# Order of precip, L seems to be important!
        precip_energy_flux = precip * L
        precip_energy_flux.convert_units(iris.unit.Unit('W m-2'))
        precip_energy_flux.rename('precip_energy_flux')
        
        filename = to_node.filename(self.computer_name, self.config)
        iris.save(precip_energy_flux, filename)

        with open(filename + '.done', 'w') as f:
            f.write('{}'.format(precip))


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
