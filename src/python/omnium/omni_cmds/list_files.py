"""List all files for config"""
import os
from glob import glob

ARGS = [(['--full-path'], {'help': 'show full path of files',
                           'action': 'store_true',
                           'default': False}),
        ]

def main(args, config):
    settings = config.settings
    full_glob = os.path.join(settings.work_dir, config.streams.glob_nc3)
    for fn in sorted(glob(full_glob)):
        if args.full_path:
            print(fn)
        else:
            print(os.path.basename(fn))


