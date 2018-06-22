"""`cat`s a file from a remote suite"""
import os
from logging import getLogger

from omnium.syncher import Syncher

logger = getLogger('om.file_cat')

ARGS = [(['filename'], {'help': 'Filenames to cat', 'nargs': 1}),
        (['--remote', '-r'], {'help': 'Remote'}),
        (['--verbose', '-v'], {'help': 'Set verbose mode', 'action': 'store_true'})]


def main(suite, args):
    syncher = Syncher(suite, args.remote, args.verbose)

    filename = args.filename[0]
    rel_dir = os.path.relpath(os.getcwd(), suite.suite_dir)
    rel_filename = os.path.join(rel_dir, filename)
    output = syncher.file_cat(rel_filename)

    print('Output from: {} ({}:{})'.format(syncher.remote_name,
                                           syncher.remote_host,
                                           os.path.join(syncher.remote_base_path, suite.name)))
    print('')
    print(output)
