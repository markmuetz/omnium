"""Remove all symlinks in suite-dir"""
import os
from logging import getLogger

logger = getLogger('om.clean_sym')

ARGS = [(['--dry-run', '-d'], {'help': 'Dry run', 'action': 'store_true'})]


def main(suite, args):
    cwd = os.getcwd()
    os.chdir(suite.suite_dir)

    total = 0
    for root, dirs, filenames in os.walk('.'):
        path = root.split(os.sep)
        for filename in filenames:
            full_filename = os.path.join(root, filename)
            if os.path.islink(full_filename):
                if os.path.realpath(full_filename) == suite.missing_file_path:
                    logger.debug('removing link: {}', full_filename)
                    total += 1
                    if not args.dry_run:
                        os.remove(full_filename)

    os.chdir(cwd)

    if args.dry_run:
        logger.info('Dry run, no links were harmed.')
        logger.info('Would have removed {} symlinks', total)
    else:
        logger.info('Removed {} symlinks', total)
