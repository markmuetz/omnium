"""List all files for config"""
import os
from glob import glob

ARGS = [(['--full-path'], {'help': 'show full path of files',
                           'action': 'store_true',
                           'default': False}),
        ]

def main(args, config):
    settings = config.settings
    for group_name in config.groups.options():
        group_sec = getattr(config, group_name)
        if hasattr(group_sec, 'filename_glob'):
            filename_glob = group_sec.filename_glob
            full_glob = os.path.join(settings.work_dir, filename_glob)
            for fn in sorted(glob(full_glob)):
                if args.full_path:
                    print(fn)
                else:
                    print(os.path.basename(fn))
