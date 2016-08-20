"""List all files for config"""
import os
from glob import glob

ARGS = [(['--full-path'], {'help': 'show full path of files',
                           'action': 'store_true',
                           'default': False}),
        ]

def main(args, config):
    settings = config.settings
    for opt in config.groups.options():
        file_glob = getattr(config.groups, opt)
        full_glob = os.path.join(settings.work_dir, file_glob)
        for fn in sorted(glob(full_glob)):
            if args.full_path:
                print(fn)
            else:
                print(os.path.basename(fn))
