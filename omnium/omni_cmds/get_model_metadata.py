"""Gets UM metadata by grabbing files/info from UM model dirs"""
import os
from logging import getLogger

from omnium import um_metadata

logger = getLogger('omni')

ARGS = [(['--dirname'], {'help': 'Dir in config to search from',
                         'default': 'work'}),
        (['--out-dirname'], {'help': 'Dir in config to store metadata in',
                             'default': 'output'}),
        (['--ignore-required'], {'help': 'Don\'t fail if required file not found',
                                 'action': 'store_true'})]


def main(args, config, process_classes):
    computer_name = config['computer_name']

    dirs = config['computers'][computer_name]['dirs']
    try:
        start_dir = dirs[args.dirname]
        output_dir = dirs[args.out_dirname]
    except KeyError:
        logger.warn('Dir not in config: {}'.format(args.dirname))
        logger.info('Choices for --dirname are: ')
        for key in dirs.keys():
            logger.info('  ' + key)
        return 1

    out_dir = os.path.join(output_dir, 'model_metadata')
    logger.debug('Using start_dir: {}'.format(start_dir))
    logger.debug('Using out_dir: {}'.format(out_dir))

    model_dir = um_metadata.find_model_dir(start_dir)
    found_files = um_metadata.find_metadata_in_model_dir(model_dir, args.ignore_required)
    um_metadata.copy_found_files(model_dir, out_dir, found_files)
