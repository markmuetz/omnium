import os
from glob import glob

from omnium.syncher import Syncher
from omnium.suite import Suite

ARGS = [(['filenames'], {'help': 'Filenames to fetch', 'nargs': '+'}),
        (['--remote', '-r'], {'help': 'Remote'}),
        (['--verbose', '-v'], {'help': 'Set verbose mode', 'action': 'store_true'})]


def main(args):
    suite = Suite()
    suite.load(os.getcwd())

    syncher = Syncher(suite, args.remote, args.verbose)

    filenames = args.filenames
    rel_filenames = []
    rel_dir = os.path.relpath(os.getcwd(), suite.suite_dir)
    rel_filenames = [os.path.join(rel_dir, fn) for fn in sorted(filenames)]
    syncher.fetch(rel_filenames)
