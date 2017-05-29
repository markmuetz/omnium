import os
import subprocess as sp
from logging import getLogger

from omnium.omnium_errors import OmniumError

logger = getLogger('omnium')


class Syncher(object):
    "Provides means for syncing files from a remote host to a mirror"

    # 1st --exclude: must come *before* includes or e.g. .omnium/suite.conf will be downloaded.
    # 2nd --exclude: makes sure that only the filetypes asked for are downloaded.
    cmd_fmt = ("rsync -zuar{verbose} --exclude '.omnium/' {progress} {include} "
               "--exclude '*' --prune-empty-dirs {host}:{path}/ {dst_suite}")

    def __init__(self, suite, host=None, base_path='work/cylc-run', verbose=False):
        self.suite = suite
        self.host = host
        self.base_path = base_path
        self.verbose = 'v' if verbose else ''
        self.progress = '--progress' if verbose else ''
        # First include is necessary to make sure all dirs are included?
        # Gets configuration, python, shell scripts, info, cylc suite, and logs by default.
        self.includes = ['*/', '*.conf', '*.py', '*.sh', '*.info',
                         'suite*rc*', 'log*Z', 'log*.tar.gz']
        if self.suite.is_in_suite:
            if not host:
                if self.suite.suite_config['settings']['suite_type'] == 'mirror':
                    remote_config = self.suite.suite_config['remote']
                    self.host = remote_config['host']
                    logger.debug('Set host to: {}'.format(self.host))

    def add_exts(self, exts):
        "Add extensions to sync from remote host to mirror"
        self.includes.extend(['*' + ext for ext in exts])

    def _sync(self, suite_name, dst_suite):
        include = ' '.join(["--include '{}'".format(inc) for inc in self.includes])

        path = os.path.join(self.base_path, suite_name)
        cmd = self.cmd_fmt.format(verbose=self.verbose,
                                  progress=self.progress,
                                  include=include,
                                  host=self.host,
                                  path=path,
                                  dst_suite=dst_suite)

        logger.debug(cmd)
        sp.call(cmd, shell=True)

    def create(self, suite_name):
        "Creates a suite, filled with files from remote host"
        logger.info('Creating suite mirror: {}'.format(suite_name))
        self._sync(suite_name, suite_name)
        logger.info('Created')

    def sync(self):
        "Syncs a suite with files from remote host, must be used within a suite"
        if not self.suite.is_in_suite:
            raise OmniumError('Sync can only be used with a valid suite')
        if self.suite.suite_config['settings']['suite_type'] != 'mirror':
            raise OmniumError('Sync can only be used with a suite that is a mirror')

        remote_config = self.suite.suite_config['remote']
        if remote_config['host'] != self.host:
            msg_fmt = 'omnium config host different to requested host: {}, {}'
            logger.warn(msg_fmt.format(remote_config['host'], self.host))

        logger.info("Sync'ing suite mirror: {}".format(self.suite.name))

        logger.debug('cd to {}'.format(self.suite.suite_dir))
        cwd = os.getcwd()
        os.chdir(self.suite.suite_dir)

        self._sync(self.suite.name, '.')

        logger.debug('cd back to {}'.format(cwd))
        os.chdir(cwd)

        logger.info("Sync'd")
