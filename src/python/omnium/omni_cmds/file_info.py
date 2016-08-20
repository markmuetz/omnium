"""Print info about a given file"""
import os
from glob import glob

import iris

ARGS = [(['--full-path'], {'help': 'show full path of files',
                           'action': 'store_true',
                           'default': False}),
        (['filename'], {'help': 'File to get info for ', }),
        ]

def main(args, config):
    settings = config.settings
    full_glob = os.path.join(settings.work_dir, config.groups.glob_nc3)
    cubes = None
    if args.full_path:
        cubes = iris.load(args.filename)
    else:
        for fn in sorted(glob(full_glob)):
            if os.path.basename(fn) == args.filename:
                cubes = iris.load(fn)
                break
    if not cubes:
        raise Exception('No cubes with filename {} found'.format(args.filename))

    for cube in cubes:
        cube_stash = cube.attributes['STASH']
        section, item = cube_stash.section, cube_stash.item
        #stash_name = self.stash_vars[section][item]
        print('{0:>4}{1:>4} {2}'.format(section, item, cube.shape))
        print(cube)



