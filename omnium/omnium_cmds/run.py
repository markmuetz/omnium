"""Lists all omnis"""
from __future__ import print_function
import os
from glob import glob

ARGS = [(['procs'], {'nargs': '+'}),
        (['filename'], {'nargs': 1})]


def main(args):
    user_dir = os.path.expandvars('$HOME')
    omnium_dir = os.path.join(user_dir, 'omnium')
    print(os.environ.keys())
    print(os.getenv('AVOID_MIMAS'))
    print(os.getcwd())
    print(__file__)
    print(args.procs)
    print(args.filename)

    with open('rose-app-run.conf', 'r') as f:
        for l in f.readlines():
            print(l, end='')

    for proc_name in args.procs:
        proc_filename = os.path.join(omnium_dir, proc_name + '.py')
        assert os.path.exists(proc_filename)
        print(proc_filename)
