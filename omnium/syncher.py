import os
import subprocess as sp
from collections import OrderedDict
from logging import getLogger

from omnium.omnium_errors import OmniumError
from omnium.utils import cd

logger = getLogger('om.syncher')


class Syncher(object):
    """Provides means for syncing files from a remote suite to a mirror

    The remote suite can be on a local computer.
    """

    index_file_fmt = ".omnium/{}.file_index.txt"

    local_send_cmd_fmt = ("rsync -Rza{verbose} {rel_filenames} {path}/")
    local_fetch_cmd_fmt = ("rsync -Rza{verbose} {progress} {rel_filenames} .")
    local_sync_cmd_fmt = ('MYPWD=`pwd` && cd {path} && find . -type f '
                          '> $MYPWD/.omnium/{remote_name}.file_index.txt '
                          '2> $MYPWD/.omnium/sync.errlog')
    local_info_cmd_fmt = ('cd {path} && ls -lh {rel_filenames}')
    local_cat_cmd_fmt = ('cd {path} && cat {rel_filename}')
    local_run_cmd_fmt = ('cd {path} && {cmd}')
    # 1st --exclude: must come *before* includes or e.g. .omnium/suite.conf will be downloaded.
    # 2nd --exclude: makes sure that only the filetypes asked for are downloaded.
    local_clone_cmd_fmt = ("rsync -zuar{verbose} --exclude '.omnium/' {progress} {include} "
                           "--exclude '*' {path}/ {dst_suite}")

    remote_send_cmd_fmt = ("rsync -Rza{verbose} {rel_filenames} {host}:{path}/")
    remote_fetch_cmd_fmt = ("rsync -Rza{verbose} {progress} {host}:{rel_filenames} .")
    remote_sync_cmd_fmt = ('ssh {host} "cd {path} && find . -type f"'
                           '> .omnium/{remote_name}.file_index.txt {ignore_stderr}')
    remote_info_cmd_fmt = ('ssh {host} "cd {path} && ls -lh {rel_filenames}"')
    remote_cat_cmd_fmt = ('ssh {host} "cd {path} && cat {rel_filename}"')
    remote_run_cmd_fmt = ('ssh {host} "cd {path} && {cmd}"')
    # 1st --exclude: must come *before* includes or e.g. .omnium/suite.conf will be downloaded.
    # 2nd --exclude: makes sure that only the filetypes asked for are downloaded.
    remote_clone_cmd_fmt = ("rsync -zuar{verbose} --exclude '.omnium/' {progress} {include} "
                            "--exclude '*' {host}:{path}/ {dst_suite}")

    def __init__(self, suite, remote_name=None, verbose=False):
        self.suite = suite

        self.verbose = 'v' if verbose else ''
        self.progress = '--progress' if verbose else ''

        if not remote_name:
            remote_name = suite.settings['default_remote']
        self.local = remote_name == 'localhost'

        self.remote_name = remote_name
        self.remote = suite.suite_config['remote "{}"'.format(remote_name)]
        self.remote_host = self.remote['host']
        self.remote_base_path = self.remote['base_path']
        logger.debug('remote_name: {}', self.remote_name)
        logger.debug('remote_host: {}', self.remote_host)
        logger.debug('remote_base_path: {}', self.remote_base_path)

    def clone(self):
        includes = ['*/', '*.conf', '*.py', '*.sh', '*.info', 'suite*rc*', 'log*Z', 'log*.tar.gz']
        include = ' '.join(["--include '{}'".format(inc) for inc in includes])

        path = os.path.join(self.remote_base_path, self.suite.name)
        cmd = self._format_cmd('clone',
                               verbose=self.verbose,
                               progress=self.progress,
                               include=include,
                               host=self.remote_host,
                               path=path,
                               dst_suite=self.suite.name)
        sp.call(cmd, shell=True)

    def sync(self):
        "Syncs a suite with files from remote host, must be used within a suite"
        if not self.suite.is_in_suite:
            raise OmniumError('Sync can only be used with a valid suite')
        if self.suite.suite_config['settings']['suite_type'] != 'mirror':
            raise OmniumError('Sync can only be used with a suite that is a mirror')

        logger.info("Sync'ing suite mirror: {}", self.suite.name)

        with cd(self.suite.suite_dir):
            self._sync()

        logger.info("Sync'd")

    def send(self, rel_filenames):
        path = os.path.join(self.remote_base_path, self.suite.name)
        cmd = self._format_cmd('send',
                               verbose=self.verbose,
                               rel_filenames=' '.join(rel_filenames),
                               host=self.remote_host,
                               path=os.path.join(path))

        with cd(self.suite.suite_dir):
            sp.call(cmd, shell=True)

    def fetch(self, rel_filenames):
        with cd(self.suite.suite_dir):
            remote_rel_filenames = self._find_remote_rel_filenames(rel_filenames)
            cmd = self._format_cmd('fetch',
                                   verbose=self.verbose,
                                   progress=self.progress,
                                   rel_filenames=' :'.join(remote_rel_filenames),
                                   host=self.remote_host)

            sp.call(cmd, shell=True)

    def file_info(self, rel_filenames):
        path = os.path.join(self.remote_base_path, self.suite.name)
        cmd = self._format_cmd('info',
                               path=path,
                               rel_filenames=' '.join(rel_filenames),
                               host=self.remote_host)

        with cd(self.suite.suite_dir):
            output = sp.check_output(cmd, shell=True)
        logger.debug(output)
        return output.decode('utf-8').split('\n')[:-1]

    def file_cat(self, rel_filename):
        os.chdir(self.suite.suite_dir)

        path = os.path.join(self.remote_base_path, self.suite.name)
        cmd = self._format_cmd('cat',
                               path=path,
                               rel_filename=rel_filename,
                               host=self.remote_host)

        output = sp.check_output(cmd, shell=True)
        logger.debug(output)
        return output

    def run_cmd(self, rel_dir, remote_cmd):
        path = os.path.join(self.remote_base_path, self.suite.name, rel_dir)
        cmd = self._format_cmd('run',
                               path=path,
                               host=self.remote_host,
                               cmd=remote_cmd)
        output = sp.check_output(cmd, shell=True)
        return path, output

    def _find_remote_rel_filenames(self, rel_filenames):
        remote_index_file = self.index_file_fmt.format(self.remote_name)
        if not os.path.exists(remote_index_file):
            logger.info('No remote index for "{}", syncing', self.remote_name)
            self.sync()

        with open(remote_index_file, 'r') as f:
            remote_index = OrderedDict([(l.strip(), 1) for l in f.readlines()])

        for rel_filename in rel_filenames:
            if os.path.isdir(rel_filename):
                continue

            rel_filename = os.path.normpath(rel_filename)
            if rel_filename[:2] != './':
                dot_rel_filename = './' + rel_filename
            else:
                dot_rel_filename = rel_filename
            if dot_rel_filename not in remote_index:
                logger.debug('File not in "{}" index: {}', self.remote_name, rel_filename)
                rel_filenames.remove(rel_filename)

        if not rel_filenames:
            logger.warning('No files to fetch')
            return

        remote_suite_path = os.path.join(self.remote_base_path, self.suite.name)
        # The '.' is important: it tells rsync what to use as its relative path.
        remote_rel_filenames = [os.path.join(remote_suite_path, '.', fn) for fn in rel_filenames]
        return remote_rel_filenames

    def _local_sync(self):
        path = os.path.join(self.remote_base_path, self.suite.name)
        ignore_stderr = ''
        cmd = self.local_sync_cmd_fmt.format(host=self.remote_host,
                                             path=path,
                                             remote_name=self.remote_name,
                                             ignore_stderr=ignore_stderr)
        sp.call(cmd, shell=True)
        with open(self.index_file_fmt.format(self.remote_name), 'r') as f:
            lines = [l.strip() for l in f.readlines()]
        logger.debug('found {} remote files', len(lines))

        logger.info('Creating symlinks')
        count = 0
        for line in lines:
            dirname = os.path.dirname(line)
            if not os.path.exists(dirname):
                logger.debug('Adding dir: {}', dirname)
                os.makedirs(dirname)
                print('{}/'.format(dirname))
            if not (os.path.exists(line) or os.path.islink(line)):
                logger.debug('Adding symlink: {}', line)
                rel_path = os.path.relpath(self.suite.missing_file_path, os.path.dirname(line))
                os.symlink(rel_path, line)
                count += 1
                print('{}'.format(line))
        logger.info('Created {} symlinks', count)

    def _format_cmd(self, cmd_name, **kwargs):
        fmt_cmd_name = '{}_{}_cmd_fmt'.format('local' if self.local else 'remote', cmd_name)
        cmd_fmt = getattr(self, fmt_cmd_name)
        cmd = cmd_fmt.format(**kwargs)
        logger.debug(cmd)
        return cmd

    def _sync(self):
        path = os.path.join(self.remote_base_path, self.suite.name)
        ignore_stderr = '2>.omnium/sync.errlog'
        cmd = self._format_cmd('sync',
                               host=self.remote_host,
                               path=path,
                               remote_name=self.remote_name,
                               ignore_stderr=ignore_stderr)
        sp.call(cmd, shell=True)
        with open(self.index_file_fmt.format(self.remote_name), 'r') as f:
            lines = [l.strip() for l in f.readlines()]
        logger.debug('found {} remote files', len(lines))

        logger.info('Creating symlinks')
        count = 0
        for line in lines:
            dirname = os.path.dirname(line)
            if not os.path.exists(dirname):
                logger.debug('Adding dir: {}', dirname)
                os.makedirs(dirname)
                print('{}/'.format(dirname))
            if not (os.path.exists(line) or os.path.islink(line)):
                logger.debug('Adding symlink: {}', line)
                rel_path = os.path.relpath(self.suite.missing_file_path, os.path.dirname(line))
                os.symlink(rel_path, line)
                count += 1
                print('{}'.format(line))
        logger.info('Created {} symlinks', count)
