import os
import re
from logging import getLogger

import iris
import iris.util
try:
    import cf_units as units
except ImportError:
    import iris.unit as units

from omnium.processes import Process

logger = getLogger('omni')

class IrisProcess(Process):
    num_files = 'single'

    def load(self):
        super(IrisProcess, self).load()
        assert(len(self.node.from_nodes) == 1)

        from_node = self.node.from_nodes[0]

        if self.num_vars == 'single':
            cbs = iris.load(from_node.filename(self.config))
            assert(len(cbs) == 1)
            self.data = cbs[0]
        elif self.num_vars == 'multi':
            self.data = iris.load(from_node.filename(self.config))

        return self.data

    def save(self):
        super(IrisProcess, self).save()
        filename = self.node.filename(self.config)
        iris.save(self.processed_data, filename)
        self.saved = True
        return filename


class DomainMean(IrisProcess):
    name = 'domain_mean'
    out_ext = 'nc'
    num_vars = 'multi'

    def load(self):
        super(IrisProcess, self).load()

        first_node = self.node.from_nodes[0]
        filename = first_node.filename(self.config)
        cubes = iris.load(filename)
	found = False
        for cube in cubes:
            cube_stash = cube.attributes['STASH']
	    logger.debug(cube_stash)
            section, item = cube_stash.section, cube_stash.item
            if section == self.node.section and item == self.node.item:
		found = True
                break

	if not found:
	    raise Exception('Could not find {}'.format(self.node))

        self.cube = cube
        coords = ['grid_latitude', 'grid_longitude']
        for coord_name in coords:
            try:
                coord = cube.coord(coord_name)
            except iris.exceptions.CoordinateNotFoundError:
                raise Exception('Cube does not have coord {}'.format(coord_name))

        varname = cube.name()
        def cube_iter():
            for from_node in self.node.from_nodes:
                filename = from_node.filename(self.config)
                logger.debug('Loading cube {}'.format(filename))
                yield iris.load(filename, varname)[0]

        self.data = cube_iter()

    def run(self):
        super(DomainMean, self).run()
        all_cubes = self.data

        results = []
        for cube in all_cubes:
            result = cube.collapsed(['grid_latitude', 'grid_longitude'], 
                                    iris.analysis.MEAN)
            results.append(result)

        results_cube = iris.cube.CubeList(results).concatenate_cube()
        self.processed_data = results_cube
        return results_cube


class ConvertPpToNc(IrisProcess):
    name = 'convert_pp_to_nc'
    out_ext = '.nc'
    num_vars = 'multi'

    @staticmethod
    def convert_filename(filename):
        # e.g. atmos.000.pp3 => atmos.000.3.nc
        filename = os.path.basename(filename)
        if not re.match('pp\d', filename[-3:]):
            raise Exception('Unrecognized filename {}'.format(filename))

        pre, ext = os.path.splitext(filename)

        return pre + '.' + ext[-1] + ConvertPpToNc.out_ext 


    def run(self):
        super(ConvertPpToNc, self).run()
        cubes = self.data
        if not len(cubes):
            logger.warn('Cubes is empty')
            return
        self.processed_data = cubes
        return cubes


class TimeDelta(IrisProcess):
    name = 'time_delta'
    out_ext = 'nc'
    num_vars = 'single'

    def run(self):
        super(TimeDelta, self).run()
        field = self.data
        deltas = iris.util.delta(field.data, 0)

        deltas_cube = field[1:].copy()
        deltas_cube.data = deltas
        deltas_cube.rename(field.name() + '_time_delta')

        self.processed_data = deltas_cube
        return deltas_cube


class ConvertMassToEnergyFlux(IrisProcess):
    name = 'convert_mass_to_energy_flux'
    out_ext = 'nc'
    num_vars = 'single'

    def run(self):
        super(ConvertMassToEnergyFlux, self).run()
        precip = self.data

        L = iris.cube.Cube(2.5e6, long_name='latent_heat_of_evap', units='J kg-1')
	# Order of precip, L seems to be important!
        precip_energy_flux = precip * L
        precip_energy_flux.convert_units(units.Unit('W m-2'))
        precip_energy_flux.rename('precip_energy_flux')

        self.processed_data = precip_energy_flux
        return precip_energy_flux