import os
import re
from collections import OrderedDict
from logging import getLogger

logger = getLogger('omnium')


class Stash(OrderedDict):
    def __init__(self):
        super(Stash, self).__init__()
        omnium_home = os.path.dirname(os.path.realpath(__file__))
        stash_master_path = os.path.join(omnium_home, 'data/files/vn10.5/STASHmaster_A')
        # stash_master_path = 'files/vn10.5/STASHmaster_A'

        with open(stash_master_path) as f:
            lines = f.readlines()

        for name_line in [l for l in lines if l[0] == '1']:
            split_line = [s.strip() for s in name_line.split('|')]
            section = int(split_line[2])
            if section not in self:
                self[section] = OrderedDict()
            item = int(split_line[3])
            name = split_line[4]
            self[section][item] = name

    def search(self, search):
        results = []
        for section, section_dict in self.items():
            for item, name in section_dict.items():
                if re.search(search, name, re.IGNORECASE):
                    results.append(((section, item), name))
        return results

    def get_name(self, section, item):
        return self[section][item]

    def rename_unknown_cubes(self, cubes, force=False):
        for cube in cubes:
            self.rename_unknown_cube(cube, force)

    def rename_unknown_cube(self, cube, force=False):
        if force or cube.name()[:7] == 'unknown':
            section = cube.attributes['STASH'].section
            item = cube.attributes['STASH'].item
            name = self[section][item]
            logger.info('Renaming {}->{}'.format(cube.name(), name))
            cube.rename(name)
