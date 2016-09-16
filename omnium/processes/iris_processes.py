import os
import re
from logging import getLogger
import importlib

import numpy as np

from processes import Process

logger = getLogger('omni')


class IrisProcess(Process):
    num_vars = 'single'
    num_files = 'single'
    out_ext = 'nc'

    def load_modules(self):
        self.iris = importlib.import_module('iris')
        self.iris_util = importlib.import_module('iris.util')
        try:
            self.units = importlib.import_module('cf_units')
        except ImportError:
            self.units = importlib.import_module('iris.unit')

    def load_upstream(self):
        super(IrisProcess, self).load_upstream()
        assert(len(self.node.from_nodes) == 1)

        from_node = self.node.from_nodes[0]

        if self.num_vars == 'single':
            cbs = self.iris.load(from_node.filename(self.config))
            assert(len(cbs) == 1)
            self.data = cbs[0]
        elif self.num_vars == 'multi':
            self.data = self.iris.load(from_node.filename(self.config))

        return self.data

    def find_cube(self, section_item=None):
        if not section_item:
            section, item = self.node.section, self.node.item
        else:
            section, item = section_item

        first_node = self.node.from_nodes[0]
        filename = first_node.filename(self.config)
        cubes = self.iris.load(filename)
        found = False
        for cube in cubes:
            cube_stash = cube.attributes['STASH']
            logger.debug(cube_stash)
            cube_section, cube_item = cube_stash.section, cube_stash.item
            if cube_section == section and cube_item == item:
                found = True
                break

        if not found:
            raise Exception('Could not find {}'.format(self.node))
        return cube

    def save(self):
        super(IrisProcess, self).save()
        filename = self.node.filename(self.config)
        self.iris.save(self.processed_data, filename)
        self.saved = True
        return filename


class DomainMean(IrisProcess):
    name = 'domain_mean'
    num_vars = 'multi'

    def load_upstream(self):
        super(IrisProcess, self).load_upstream()  # pylint: disable=bad-super-call
        cube = self.find_cube()
        coords = ['grid_latitude', 'grid_longitude']
        for coord_name in coords:
            try:
                coord = cube.coord(coord_name)
            except self.iris.exceptions.CoordinateNotFoundError:
                raise Exception('Cube does not have coord {}'.format(coord_name))

        varname = cube.name()

        def cube_iter():
            for from_node in self.node.from_nodes:
                filename = from_node.filename(self.config)
                logger.debug('Loading cube {}'.format(filename))
                yield self.iris.load(filename, varname)[0]

        self.data = cube_iter()

    def run(self):
        super(DomainMean, self).run()
        all_cubes = self.data

        results = []
        for cube in all_cubes:
            result = cube.collapsed(['grid_latitude', 'grid_longitude'],
                                    self.iris.analysis.MEAN)
            results.append(result)

        results_cube = self.iris.cube.CubeList(results).concatenate_cube()
        self.processed_data = results_cube
        return results_cube


class Combine(IrisProcess):
    name = 'combine'
    num_vars = 'multi'

    def load_upstream(self):
        super(IrisProcess, self).load_upstream()  # pylint: disable=bad-super-call
        cube = self.find_cube()
        coords = ['grid_latitude', 'grid_longitude']
        for coord_name in coords:
            try:
                coord = cube.coord(coord_name)
            except self.iris.exceptions.CoordinateNotFoundError:
                raise Exception('Cube does not have coord {}'.format(coord_name))

        varname = cube.name()

        def cube_iter():
            for from_node in self.node.from_nodes:
                filename = from_node.filename(self.config)
                yield self.iris.load(filename, varname)[0]

        self.data = cube_iter()

    def run(self):
        super(Combine, self).run()
        all_cubes = self.data

        results = []
        for cube in all_cubes:
            result = cube
            results.append(result)

        results_cube = self.iris.cube.CubeList(results).concatenate_cube()
        self.processed_data = results_cube
        return results_cube


class ConvertPpToNc(IrisProcess):
    name = 'convert_pp_to_nc'
    out_ext = 'nc'
    num_vars = 'multi'

    @staticmethod
    def convert_filename(filename):
        # e.g. atmos.000.pp3 => atmos.000.3.nc
        filename = os.path.basename(filename)
        if not re.match('pp\d', filename[-3:]):
            raise Exception('Unrecognized filename {}'.format(filename))

        pre, ext = os.path.splitext(filename)

        return pre + '.' + ext[-1] + '.' + ConvertPpToNc.out_ext

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
    num_vars = 'single'

    def run(self):
        super(TimeDelta, self).run()
        field = self.data
        deltas = self.iris_util.delta(field.data, 0)

        deltas_cube = field[1:].copy()
        deltas_cube.data = deltas
        deltas_cube.rename(field.name() + '_time_delta')

        self.processed_data = deltas_cube
        return deltas_cube


class ConvertMassToEnergyFlux(IrisProcess):
    name = 'convert_mass_to_energy_flux'
    num_vars = 'single'

    def run(self):
        super(ConvertMassToEnergyFlux, self).run()
        precip = self.data
        precip_units = self.units.Unit('kg m-2 s-1')
        if not precip.units == precip_units:
            raise Exception('Cube {} has the wrong units, is {}, should be {}'
                            .format(precip.name(), precip.units, precip_units))

        L = self.iris.cube.Cube(2.5e6, long_name='latent_heat_of_evap', units='J kg-1')
        # Order of precip, L seems to be important!
        precip_energy_flux = precip * L
        precip_energy_flux.convert_units(self.units.Unit('W m-2'))
        precip_energy_flux.rename('precip_energy_flux')

        self.processed_data = precip_energy_flux
        return precip_energy_flux


class MassWeightedVerticalIntegral(IrisProcess):
    name = 'mass_weighted_vertical_integral'
    num_vars = 'multi'
    # Radius of Earth.
    R = 6371229.

    def load_upstream(self):
        super(IrisProcess, self).load_upstream()  # pylint: disable=bad-super-call
        cube = self.find_cube()
        rho_R2 = self.find_cube((0, 253))
        coords = ['grid_latitude', 'grid_longitude']
        for coord_name in coords:
            try:
                coord = cube.coord(coord_name)
            except self.iris.exceptions.CoordinateNotFoundError:
                raise Exception('Cube does not have coord {}'.format(coord_name))

        varname = cube.name()
        rhoname = rho_R2.name()

        def cube_iter():
            for from_node in self.node.from_nodes:
                filename = from_node.filename(self.config)
                logger.debug('Loading cube {}'.format(filename))
                iter_rho_R2 = self.iris.load(filename, rhoname)[0]
                iter_cube = self.iris.load(filename, varname)[0]
                yield iter_rho_R2, iter_cube

        self.data = cube_iter()

    def run(self):
        super(MassWeightedVerticalIntegral, self).run()

        results = []

        for rho_R2, cube in self.data:
            cube_heights = cube.coord('level_height').points
            rho_heights = rho_R2.coord('level_height').points
            rho = rho_R2.data / self.R**2

            if len(cube_heights) != len(rho_heights) + 1:
                raise Exception('Cube {} not on theta level'.format(cube.name()))

            cube_heights_on_rho = (cube_heights[:-1] + cube_heights[1:]) / 2
            isclose = np.isclose(cube_heights_on_rho, rho_heights)
            if not isclose.all():   # pylint: disable=no-member
                raise Exception('Interpolation of cube heights failed')

            # Work out dz, turn into 4d field to be multiplied by data.
            dz = cube_heights[1:] - cube_heights[:-1]
            dz3d = dz.repeat(cube.shape[2] * cube.shape[3])\
                     .reshape(cube.shape[1] - 1, cube.shape[2], cube.shape[3])
            dz4d = np.tile(dz3d, (cube.shape[0], 1, 1, 1))  # pylint: disable=no-member

            # Work out variable on rho grid, perform integral.
            variable_on_rho_grid_data = (cube.data[:, :-1] + cube.data[:, 1:]) / 2
            # Assume bottom rho level value equal to bottom theta level value
            # cf:
            # https://code.metoffice.gov.uk/trac/um/browser/main/branches/dev/chrissmith/
            # vn10.5_ium_base/src/atmosphere/energy_correction/
            # vert_eng_massq-vrtemq1b.F90?rev=24919#L297
            # N.B. has no effect on outcome for data that I have analysed so far:
            # np.isclose(cube.data[:, 0], cube.data[:, 1]).all() == True
            # Therefore adding and averaging is the same as just taking one of them.
            variable_on_rho_grid_data[:, 0] = cube.data[:, 0]
            variableXrho = variable_on_rho_grid_data * rho
            variable_col = ((dz4d * variableXrho)[:, :]).sum(axis=1)

            # Stuff results into a lovingly crafted cube.
            new_cube = cube.slices_over('model_level_number').next().copy()
            new_cube.data = variable_col
            new_cube.rename('Mass weighted vertical integral of {}'.format(cube.name()))
            new_cube.units = 'kg m-2'
            results.append(new_cube)

        results_cube = self.iris.cube.CubeList(results).concatenate_cube()
        self.processed_data = results_cube

        return self.processed_data
