"""Lists all omnis"""
import os
from glob import glob

ARGS = [(['--full-path'], {'help': 'show full path of files',
                           'action': 'store_true',
                           'default': False}),
        ]

def main(args):
    user_dir = os.path.expandvars('$HOME')
    omnis_dir = os.path.join(user_dir, 'omnis')
    for dirname in sorted(glob(os.path.join(omnis_dir, '*'))):
        if args.full_path:
            print(dirname)
        else:
            print(os.path.basename(dirname))

