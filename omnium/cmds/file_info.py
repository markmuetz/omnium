"""Retrieves file information from remote suite"""
import os
from logging import getLogger

from omnium.syncher import Syncher

logger = getLogger('om.file_info')

ARGS = [(['filenames'], {'help': 'Filenames to fetch', 'nargs': '+'}),
        (['--remote', '-r'], {'help': 'Remote'}),
        (['--verbose', '-v'], {'help': 'Set verbose mode', 'action': 'store_true'}),
        (['--long', '-l'], {'help': 'Output ls -l', 'action': 'store_true'})]


def main(suite, args):
    syncher = Syncher(suite, args.remote, args.verbose)

    filenames = args.filenames
    rel_filenames = []
    rel_dir = os.path.relpath(os.getcwd(), suite.suite_dir)
    rel_filenames = [os.path.join(rel_dir, fn) for fn in sorted(filenames)]
    output_lines = syncher.file_info(rel_filenames)

    print('Output from: {} ({}:{})'.format(syncher.remote_name,
                                           syncher.remote_host,
                                           os.path.join(syncher.remote_base_path, suite.name)))
    print('')
    for line in output_lines:
        logger.debug(line)
        if args.long:
            print(line)
        else:
            split_line = line.split()
            print('{0:>5} {1}'.format(split_line[4], os.path.basename(split_line[-1])))
