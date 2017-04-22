import os
from glob import glob
from logging import getLogger
import shutil

logger = getLogger('omni')


def find_model_dir(start_dir):
    if not os.path.exists(start_dir):
        raise Exception('start_dir does not exist: {}'.format(start_dir))

    model_dir = start_dir
    # Walk up dirs looking for suite.rc:
    while not os.path.exists(os.path.join(model_dir, 'suite.rc')) and model_dir != '/':
        model_dir = os.path.dirname(model_dir)
    if model_dir == '/':
        raise Exception('Could not find suite.rc in or above: {}'.format(start_dir))
    logger.info('Found suite.rc in: {}'.format(model_dir))
    return model_dir


def find_metadata_in_model_dir(model_dir, ignore_required):
    found_files = []
    files_to_get = [
        ('rose-suite.info', True),
        ('suite.rc', True),
        ('suite.rc.processed', True),
        ('app/um/rose-app.conf', True),
        ('app/um/opt/*.conf', False),
        ('app/fcm_make/rose-app.conf', True),
        ('share/fcm_make/fcm-make2.cfg.orig', True),
        ('app/fcm_make/file/fcm-make.cfg', True)]
    for file_glob, required in files_to_get:
        full_file_glob = os.path.join(model_dir, file_glob)
        logger.debug('Using glob: {}'.format(full_file_glob))
        filenames = glob(full_file_glob)
        if required and not filenames:
            if not ignore_required:
                raise Exception('Could not find: {}'.format(file_glob))
            else:
                raise logger.debug('Could not find: {}'.format(file_glob))

        for filename in filenames:
            found_files.append(filename)
    return found_files


def copy_found_files(start_dir, out_dir, found_files):
    for filename in found_files:
        relpath = os.path.relpath(filename, start_dir)
        out_filename = os.path.join(out_dir, relpath)
        if not os.path.exists(os.path.dirname(out_filename)):
            os.makedirs(os.path.dirname(out_filename))
        logger.info('Copying file: {}'.format(relpath))
        logger.debug('  from: {}'.format(filename))
        logger.debug('  to  : {}'.format(out_filename))
        if os.path.exists(out_filename):
            logger.debug('  outile exists, overwriting')
        shutil.copyfile(filename, out_filename)
