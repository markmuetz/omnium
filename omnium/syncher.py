import os
import subprocess as sp
from collections import OrderedDict
from logging import getLogger

from omnium.omnium_errors import OmniumError

logger = getLogger('om.syncher')


class Syncher(object):
    "Provides means for syncing files from a remote host to a mirror"

    index_file_fmt = ".omnium/{}.file_index.txt"
    send_cmd_fmt = ("rsync -Rza{verbose} {rel_filenames} {host}:{path}/")
    fetch_cmd_fmt = ("rsync -Rza{verbose} {progress} {host}:{rel_filenames} .")
    sync_cmd_fmt = ('ssh {host} "cd {path} && find . -type f"'
                    '> .omnium/{remote_name}.file_index.txt {ignore_stderr}')
    info_cmd_fmt = ('ssh {host} "cd {path} && ls -lh {rel_filenames}"')
    cat_cmd_fmt = ('ssh {host} "cd {path} && cat {rel_filename}"')
    # 1st --exclude: must come *before* includes or e.g. .omnium/suite.conf will be downloaded.
    # 2nd --exclude: makes sure that only the filetypes asked for are downloaded.
    clone_cmd_fmt = ("rsync -zuar{verbose} --exclude '.omnium/' {progress} {include} "
                     "--exclude '*' {host}:{path}/ {dst_suite}")

    def __init__(self, suite, local=False, remote_name=None, verbose=False):
        self.suite = suite
        self.local = local
        if self.local:
            raise NotImplemented('local synching not supported yet.')

        self.verbose = 'v' if verbose else ''
        self.progress = '--progress' if verbose else ''

        if not remote_name:
            remote_name = suite.settings['default_remote']

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
        cmd = self.clone_cmd_fmt.format(verbose=self.verbose,
                                        progress=self.progress,
                                        include=include,
                                        host=self.remote_host,
                                        path=path,
                                        dst_suite=self.suite.name)
        logger.debug(cmd)
        sp.call(cmd, shell=True)

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

    def sync(self):
        "Syncs a suite with files from remote host, must be used within a suite"
        if not self.suite.is_in_suite:
            raise OmniumError('Sync can only be used with a valid suite')
        if self.suite.suite_config['settings']['suite_type'] != 'mirror':
            raise OmniumError('Sync can only be used with a suite that is a mirror')

        logger.info("Sync'ing suite mirror: {}", self.suite.name)
        logger.debug('cd to {}', self.suite.suite_dir)

        cwd = os.getcwd()
        os.chdir(self.suite.suite_dir)

        self._sync()

        logger.debug('cd back to {}', cwd)
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
        cmd = self.fetch_cmd_fmt.format(verbose=self.verbose,
                                        progress=self.progress,
                                        rel_filenames=' :'.join(remote_rel_filenames),
                                        host=self.remote_host)
        logger.debug(cmd)

        sp.call(cmd, shell=True)
        os.chdir(cwd)

    def file_info(self, rel_filenames):
        cwd = os.getcwd()
        os.chdir(self.suite.suite_dir)

        remote_index_file = self.index_file_fmt.format(self.remote_name)
        if not os.path.exists(remote_index_file):
            logger.info('No remote index for "{}", syncing', self.remote_name)
            self.sync()

        with open(remote_index_file, 'r') as f:
            remote_index = OrderedDict([(l.strip(), 1) for l in f.readlines()])

        for rel_filename in rel_filenames:
            if os.path.isdir(rel_filename):
                continue

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

        path = os.path.join(self.remote_base_path, self.suite.name)
        cmd = self.info_cmd_fmt.format(path=path,
                                       rel_filenames=' '.join(rel_filenames),
                                       host=self.remote_host)
        logger.debug(cmd)

        output = sp.check_output(cmd, shell=True)
        logger.debug(output)
        return output.decode('utf-8').split('\n')[:-1]

    def file_cat(self, rel_filename):
        # TODO: rm duplication between this, file_info and fetch
        cwd = os.getcwd()
        os.chdir(self.suite.suite_dir)

        remote_index_file = self.index_file_fmt.format(self.remote_name)
        if not os.path.exists(remote_index_file):
            logger.info('No remote index for "{}", syncing', self.remote_name)
            self.sync()

        with open(remote_index_file, 'r') as f:
            remote_index = OrderedDict([(l.strip(), 1) for l in f.readlines()])

        if os.path.isdir(rel_filename):
            return ''

        if rel_filename[:2] != './':
            rel_filename = './' + rel_filename
        if rel_filename not in remote_index:
            logger.warning('File not in "{}" index: {}', self.remote_name, rel_filename)
            return

        remote_suite_path = os.path.join(self.remote_base_path, self.suite.name)
        # The '.' is important: it tells rsync what to use as its relative path.
        # remote_rel_filenames = [os.path.join(remote_suite_path, '.', fn) for fn in rel_filenames]
        path = os.path.join(self.remote_base_path, self.suite.name)
        cmd = self.cat_cmd_fmt.format(path=path,
                                      rel_filename=rel_filename,
                                      host=self.remote_host)
        logger.debug(cmd)

        output = sp.check_output(cmd, shell=True)
        logger.debug(output)
        return output
