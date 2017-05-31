import os
import subprocess as sp
from collections import OrderedDict
from logging import getLogger

from omnium.omnium_errors import OmniumError

logger = getLogger('omnium')


class Syncher(object):
    "Provides means for syncing files from a remote host to a mirror"

    index_file_fmt = ".omnium/{}.file_index.txt"
    send_cmd_fmt = ("rsync -Rza{verbose} {rel_filenames} {host}:{path}/")
    fetch_cmd_fmt = ("rsync -Rza{verbose} {host}:{rel_filenames} .")
    sync_cmd_fmt = ('ssh {host} "cd {path} && find . -type f"'
                    '> .omnium/{remote_name}.file_index.txt {ignore_stderr}')
    info_cmd_fmt = ('ssh {host} "cd {path} && ls -lh {rel_filenames}"')
    cat_cmd_fmt = ('ssh {host} "cd {path} && cat {rel_filename}"')

    def __init__(self, suite, remote_name=None, verbose=False):
        self.suite = suite
        self.verbose = 'v' if verbose else ''
        self.progress = '--progress' if verbose else ''

        if not remote_name:
            remote_name = suite.settings['default_remote']
        self.remote_name = remote_name
        self.remote = suite.suite_config['remote "{}"'.format(remote_name)]
        self.remote_host = self.remote['host']
        self.remote_base_path = self.remote['base_path']
        logger.debug('remote_name: {}'.format(self.remote_name))
        logger.debug('remote_host: {}'.format(self.remote_host))
        logger.debug('remote_base_path: {}'.format(self.remote_base_path))

    def _sync(self):
        path = os.path.join(self.remote_base_path, self.suite.name)
        ignore_stderr = '2>.omnium/sync.errlog'
        cmd = self.sync_cmd_fmt.format(host=self.remote_host,
                                       path=path,
                                       remote_name=self.remote_name,
                                       ignore_stderr=ignore_stderr)
        logger.debug(cmd)
        sp.call(cmd, shell=True)
        with open(self.index_file_fmt.format(self.remote_name), 'r') as f:
            lines = [l.strip() for l in f.readlines()]
        logger.debug('found {} remote files'.format(len(lines)))

        logger.info('Creating symlinks')
        for line in lines:
            if (os.path.exists(os.path.dirname(line)) and not
                (os.path.exists(line) or os.path.islink(line))):
                logger.debug('Adding symlink: {}'.format(line))
                os.symlink(self.suite.missing_file_path, line)

    def sync(self):
        "Syncs a suite with files from remote host, must be used within a suite"
        if not self.suite.is_in_suite:
            raise OmniumError('Sync can only be used with a valid suite')
        if self.suite.suite_config['settings']['suite_type'] != 'mirror':
            raise OmniumError('Sync can only be used with a suite that is a mirror')

        logger.info("Sync'ing suite mirror: {}".format(self.suite.name))
        logger.debug('cd to {}'.format(self.suite.suite_dir))

        cwd = os.getcwd()
        os.chdir(self.suite.suite_dir)

        self._sync()

        logger.debug('cd back to {}'.format(cwd))
        os.chdir(cwd)

        logger.info("Sync'd")

    def send(self, rel_filenames):
        path = os.path.join(self.remote_base_path, self.suite.name)
        cmd = self.send_cmd_fmt.format(verbose=self.verbose,
                                       rel_filenames=' '.join(rel_filenames),
                                       host=self.remote_host,
                                       path=os.path.join(path))
        logger.debug(cmd)

        cwd = os.getcwd()
        os.chdir(self.suite.suite_dir)
        sp.call(cmd, shell=True)
        os.chdir(cwd)

    def fetch(self, rel_filenames):
        cwd = os.getcwd()
        os.chdir(self.suite.suite_dir)

        remote_index_file = self.index_file_fmt.format(self.remote_name)
        if not os.path.exists(remote_index_file):
            logger.info('No remote index for "{}", syncing'.format(self.remote_name))
            self.sync()

        with open(remote_index_file, 'r') as f:
            remote_index = OrderedDict([(l.strip(), 1) for l in f.readlines()])

        for rel_filename in rel_filenames:
            if os.path.isdir(rel_filename):
                continue

            if rel_filename[:2] != './':
                dot_rel_filename = './' + rel_filename
            if dot_rel_filename not in remote_index:
                logger.debug('File not in "{}" index: {}'.format(self.remote_name, rel_filename))
                rel_filenames.remove(rel_filename)

        if not rel_filenames:
            logger.warn('No files to fetch')
            return

        remote_suite_path = os.path.join(self.remote_base_path, self.suite.name)
        # The '.' is important: it tells rsync what to use as its relative path.
        remote_rel_filenames = [os.path.join(remote_suite_path, '.', fn) for fn in rel_filenames]
        cmd = self.fetch_cmd_fmt.format(verbose=self.verbose,
                                        rel_filenames=' :'.join(remote_rel_filenames),
                                        host=self.remote_host)
        logger.debug(cmd)

        sp.call(cmd, shell=True)
        os.chdir(cwd)

    def file_cat(self, rel_filename):
        # TODO: rm duplication between this, file_info and fetch
        cwd = os.getcwd()
        os.chdir(self.suite.suite_dir)

        remote_index_file = self.index_file_fmt.format(self.remote_name)
        if not os.path.exists(remote_index_file):
            logger.info('No remote index for "{}", syncing'.format(self.remote_name))
            self.sync()

        with open(remote_index_file, 'r') as f:
            remote_index = OrderedDict([(l.strip(), 1) for l in f.readlines()])

        if os.path.isdir(rel_filename):
            return ''

        if rel_filename[:2] != './':
            rel_filename = './' + rel_filename
        if rel_filename not in remote_index:
            logger.warn('File not in "{}" index: {}'.format(self.remote_name, rel_filename))
            return

        remote_suite_path = os.path.join(self.remote_base_path, self.suite.name)
        # The '.' is important: it tells rsync what to use as its relative path.
        #remote_rel_filenames = [os.path.join(remote_suite_path, '.', fn) for fn in rel_filenames]
        path = os.path.join(self.remote_base_path, self.suite.name)
        cmd = self.cat_cmd_fmt.format(path=path,
                                       rel_filename=rel_filename,
                                       host=self.remote_host)
        logger.debug(cmd)

        output = sp.check_output(cmd, shell=True)
        logger.debug(output)
        return output
