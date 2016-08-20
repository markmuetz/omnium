import os
from glob import glob
from collections import OrderedDict

import iris


class UMO(object):
    def __init__(self, config):
        self.config = config
        settings = config.settings
	self.cube_index = 0
	self.time_index = 0
	self.level_index = 0
        self.filename_index = 0
        self.all_cubes = []
        self.filenames_by_group = OrderedDict()
        for glob_name in config.groups.options():
            group_name = glob_name[5:]
            group_glob = getattr(config.groups, glob_name)

            full_glob = os.path.join(settings.work_dir, group_glob)
            self.filenames_by_group[group_name] = sorted(glob(full_glob))


    def load_cubes(self, filename):
        #self.filename_index = filename_index

        self.all_cubes = []

        self.cubes = iris.load(filename)
        for cube in self.cubes:
            self.all_cubes.append(cube)
            cube_stash = cube.attributes['STASH']
            section, item = cube_stash.section, cube_stash.item
            print('{0:>4}{1:>4} {2}'.format(section, item, cube.shape))
	self.cube = self.cubes[self.cube_index]


    def set_cube(self, group, section, item):
	cube = None
	cubes = self.all_cubes

	for test_cube in cubes:
	    cube_stash = test_cube.attributes['STASH']
	    cube_section, cube_item = cube_stash.section, cube_stash.item
	    if cube_section == section and cube_item == item:
		print('Found cube {0:>3} {1:>3}'.format(section, item))
		if cube != None:
		    print('Found duplicates')
		cube = test_cube

	if not cube:
	    raise Exception('Cannot find cube {}'.format((group, section, item)))

	self.cube = cube
        self.cube_index = self.all_cubes.index(self.cube)


    def prev_time(self):
	self.time_index -= 1
        self.check_indices_in_range()

    def next_time(self):
	self.time_index += 1
        self.check_indices_in_range()

    def prev_level(self):
	self.level_index -= 1
        self.check_indices_in_range()

    def next_level(self):
	self.level_index += 1
        self.check_indices_in_range()

    def prev_cube(self):
	self.cube_index -= 1
        self.cube_index %= len(self.all_cubes)
        self.cube = self.all_cubes[self.cube_index]
        self.check_indices_in_range()

    def next_cube(self):
	self.cube_index += 1
        self.cube_index %= len(self.all_cubes)
        self.cube = self.all_cubes[self.cube_index]
        self.check_indices_in_range()

    def check_indices_in_range(self):
        if self.time_index >= self.cube.shape[0]:
            #self.load_cubes(self.filename_index + 1)
            self.time_index = 0
        self.time_index %= self.cube.shape[0]
        if self.cube.ndim == 4:
            self.level_index %= self.cube.shape[1]

    def get_2d_slice(self):
        if self.cube.ndim == 3:
            return self.cube[self.time_index]
        elif self.cube.ndim == 4:
            return self.cube[self.time_index, self.level_index]


if __name__ == '__main__':
    umo = UMO()
