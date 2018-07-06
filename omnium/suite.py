import io
import os
import shutil
import socket
from collections import OrderedDict
from logging import getLogger

from configparser import ConfigParser

from omnium.analysers import Analysers
from omnium.omnium_errors import OmniumError

logger = getLogger('om.suite')


class Suite(object):
    suite_types = ['runcontrol', 'run', 'archive', 'mirror']

    def __init__(self, cwd, cylc_control=False):
        self.cwd = cwd
        self.cylc_control = cylc_control
        self.name = None
        self.suite_dir = None
        self.is_in_suite = False
        self.is_omnium_app = False
        self.is_init = False
        self.suite_config = None
        self.analyser_dirs = []
        self.analysis_classes = OrderedDict()
        self.analysis_hash = []
        self.analysis_status = []

        self.load(cwd)

    def __repr__(self):
        return 'Suite("{}")'.format(self.suite_dir)

    def __str__(self):
        lines = [repr(self), '', 'Suite info:']
        lines.extend(['  ' + l for l in self.info_lines()])
        if self.suite_config:
            lines.extend(['', 'Suite config:'])
            lines.extend(['  ' + l for l in self.suite_config_lines()])
        return '\n'.join(lines)

    def _is_suite_root_dir(self, path):
        if os.path.exists(os.path.join(path, '.omnium')):
            return True
        elif os.path.exists(os.path.join(path, 'rose-suite.info')):
            return True
        return False

    def load(self, cwd):
        # Distinguish between .omnium and rose-suite.conf existing.
        # Set up accordingly etc.
        suite_dir = cwd
        while not self._is_suite_root_dir(suite_dir):
            suite_dir = os.path.dirname(suite_dir)
            if os.path.dirname(suite_dir) == suite_dir:
                # at root dir: /
                return

        self.is_in_suite = True
        self.suite_dir = suite_dir
        self.name = os.path.basename(suite_dir)
        logger.debug('in suite: {}', self.suite_dir)

        # Check to see if it's already been initialized.
        config_filename = os.path.join(self.suite_dir, '.omnium/suite.conf')
        if os.path.exists(config_filename):
            self.is_init = True
            self.suite_config = ConfigParser()
            with open(config_filename, 'r') as f:
                self.suite_config.read_file(f)
            logger.debug('loaded suite config')
            self.settings = self.suite_config['settings']

        # Check for omnium app.
        if os.path.exists(os.path.join(self.suite_dir, 'app/omnium/rose-app.conf')):
            self.is_omnium_app = True
            self.app_config_path = os.path.join(self.suite_dir, 'app/omnium/rose-app.conf')
            self.app_config = ConfigParser()
            with open(self.app_config_path, 'r') as f:
                self.app_config.read_file(f)
            # I have an app config. See if I can find analysis_classes:
            logger.debug('loaded app config')

        self.missing_file_path = os.path.join(self.suite_dir, '.omnium/missing_file.txt')
        if not os.path.exists(os.path.join(self.suite_dir, '.omnium')):
            os.makedirs(os.path.join(self.suite_dir, '.omnium'), exist_ok=True)

        if not os.path.exists(self.missing_file_path):
            with open(self.missing_file_path, 'w') as f:
                # Missing files will be symlinked to this.
                f.write('Missing file, use "omnium fetch" to fetch file')

        if hasattr(self, 'settings'):
            localhost = self.settings.get('localhost', socket.gethostname())
        else:
            localhost = socket.gethostname()
        self.logging_filename = os.path.join(self.suite_dir,
                                             '.omnium/log/{}.log'.format(localhost))

        if not os.path.exists(os.path.dirname(self.logging_filename)):
            os.makedirs(os.path.dirname(self.logging_filename), exist_ok=True)

    def load_analysers(self):
        omnium_analysers_pkgs = os.getenv('OMNIUM_ANALYSER_PKGS')
        if omnium_analysers_pkgs:
            analyser_pkg_names = omnium_analysers_pkgs.split(':')
        else:
            analyser_pkg_names = []
        self.analysers = Analysers(analyser_pkg_names)
        self.analysers.find_all()
        self.analysis_hash.extend(self.analysers.analysis_hash)
        self.analysis_status.extend(self.analysers.analysis_status)
        self.analysis_classes = self.analysers.analysis_classes

    def init(self, suite_name, suite_type, host_name=None, host=None, base_path=None):
        assert suite_type in Suite.suite_types
        cwd = os.getcwd()
        self.load(cwd)
        if self.is_in_suite:
            raise OmniumError('Suite already initialized')
        else:
            if suite_name:
                if os.path.exists(suite_name):
                    raise OmniumError('dir {} already exists'.format(suite_name))
                logger.debug('creating in {}', os.path.abspath(suite_name))
                os.makedirs(suite_name)
                os.chdir(suite_name)
            elif not os.path.exists('rose-suite.info'):
                raise OmniumError('Could not find "rose-suite.info" in current dir')

        self.suite_config = ConfigParser()
        self.suite_config.add_section('settings')
        self.suite_config.set('settings', 'suite_type', suite_type)
        self.suite_config.set('settings', 'default_remote', host_name)

        if suite_type == 'mirror':
            remote_sec = 'remote "{}"'.format(host_name)
            self.suite_config.add_section(remote_sec)
            self.suite_config.set(remote_sec, 'host', host)
            self.suite_config.set(remote_sec, 'base_path', base_path)

        dotomnium_dir = '.omnium'
        os.makedirs(dotomnium_dir)
        with open(os.path.join(dotomnium_dir, 'suite.conf'), 'w') as configfile:
            self.suite_config.write(configfile)

        self.load(os.getcwd())
        os.chdir(cwd)

    def abort_if_missing(self, filename):
        if self.check_filename_missing(filename):
            raise OmniumError('File missing {}'.format(filename))

    def check_filename_missing(self, filename):
        return os.path.islink(filename) and os.path.realpath(filename) == self.missing_file_path

    def suite_config_lines(self):
        conf_text = io.StringIO()
        self.suite_config.write(conf_text)
        conf_text.seek(0)
        return [l[:-1] for l in conf_text.readlines()]

    def info_lines(self):
        with open(os.path.join(self.suite_dir, 'rose-suite.info'), 'r') as f:
            return [l[:-1] for l in f.readlines()]
