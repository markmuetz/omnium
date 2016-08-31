import os
from collections import OrderedDict

class STASH(object):
    def __init__(self):
        omni_home = os.path.expandvars('$OMNI_HOME')
        stash_master_path = os.path.join(omni_home, 'files/vn10.5/STASHmaster_A')

        with open(stash_master_path) as f:
            lines = f.readlines()

        stash_vars = OrderedDict()
        for name_line in [l for l in lines if l[0] == '1']:
            split_line = [s.strip() for s in name_line.split('|')]
            section = int(split_line[2])
            if section not in stash_vars:
                stash_vars[section] = OrderedDict()
            item = int(split_line[3])
            name = split_line[4]
            stash_vars[section][item] = name
        self.stash_vars = stash_vars

    def get_name(self, section, item):
        return self.stash_vars[section][item]

    def rename_unknown_cubes(self, cubes):
        for cube in cubes:
            self.rename_unknown_cube(cube)

    def rename_unknown_cube(self, cube):
        if cube.name()[:7] == 'unknown':
            section = cube.attributes['STASH'].section 
            item = cube.attributes['STASH'].item
            name = self.stash_vars[section][item]
            print('Renaming {}->{}'.format(cube.name(), name))
            cube.rename(name)


stash = STASH()
