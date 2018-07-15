import io
import os
import shutil
import socket
import subprocess as sp
from configparser import ConfigParser
from logging import getLogger

import omnium
from omnium.omnium_errors import OmniumError
from omnium.pkg_state import PkgState
from omnium.setup_logging import add_file_logging
from .expt import ExptList

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
        self.settings = None
        self.dotomnium_dir = '.omnium'
        self.is_readonly = True
        self.logging_filename = ''
        self.missing_file_path = ''
        self.analysis_pkgs = None
        self.expts = []

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

    @staticmethod
    def _is_suite_root_dir(path):
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

        if not os.access(self.suite_dir, os.W_OK):
            logger.warning('No write access to suite dir: {}', self.suite_dir)
            logger.warning('Has suite been frozen? Use `omnium suite-unfreeze {}`', self.suite_dir)
            return
        self.is_readonly = False

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
            # I have an app config. See if I can find analyser_classes:
            logger.debug('loaded app config')

        self.missing_file_path = os.path.join(self.suite_dir, '.omnium/missing_file.txt')
        if not os.path.exists(os.path.join(self.suite_dir, '.omnium')):
            os.makedirs(os.path.join(self.suite_dir, '.omnium'), exist_ok=True)

        if not os.path.exists(self.missing_file_path):
            with open(self.missing_file_path, 'w') as f:
                # Missing files will be symlinked to this.
                f.write('Missing file, use "omnium fetch" to fetch file')

        if hasattr(self, 'settings') and self.settings:
            localhost = self.settings.get('localhost', socket.gethostname())
        else:
            localhost = socket.gethostname()
        self.logging_filename = os.path.join(self.suite_dir,
                                             '.omnium/log/{}.log'.format(localhost))

        if not os.path.exists(os.path.dirname(self.logging_filename)):
            os.makedirs(os.path.dirname(self.logging_filename), exist_ok=True)

        self.expts = ExptList(self)
        self.expts.find_all()

    def set_analysis_pkgs(self, analysis_pkgs):
        self.analysis_pkgs = analysis_pkgs

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
                os.makedirs(suite_name, exist_ok=True)
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

        os.makedirs(self.dotomnium_dir, exist_ok=True)
        self.save_suite_config()

        self.load(os.getcwd())
        os.chdir(cwd)

    def save_suite_config(self):
        with open(os.path.join(self.dotomnium_dir, 'suite.conf'), 'w') as configfile:
            self.suite_config.write(configfile)

    def save_metadata(self, settings, output_dirname, expt_names=[]):
        metadata_dir = os.path.join(output_dirname, 'metadata')
        logger.debug('write metadata to: {}', metadata_dir)
        if not os.path.exists(metadata_dir):
            os.makedirs(metadata_dir, exist_ok=True)

        settings_filename = os.path.join(metadata_dir, 'settings.json')
        settings.save(settings_filename)

        suite_filename = os.path.join(metadata_dir, 'suite_{}_info.txt'.format(self.name))
        with open(suite_filename, 'w') as f:
            f.write('name: {}\n'.format(self.name))
            for line in self.info_lines():
                f.write('{}\n'.format(line))

        computer_name = socket.gethostname()
        computer_filename = os.path.join(metadata_dir, 'comp_{}_info.txt'.format(computer_name))
        with open(computer_filename, 'w') as f:
            f.write('hostname: {}\n'.format(computer_name))
            f.write('suite_dir: {}\n'.format(self.suite_dir))
            f.write('cwd: {}\n'.format(os.getcwd()))
            f.write('ENV:\n')
            for env_key, env_val in os.environ.items():
                f.write('  {}={}\n'.format(env_key, env_val))

        if expt_names:
            expts = ExptList(self)
            expts.find(expt_names)
            for expt in expts:
                rose_app_run_conf_file = os.path.join(metadata_dir,
                                                      '{}_rose-app-run.conf'.format(expt.name))
                shutil.copy(expt.rose_app_run_conf_file, rose_app_run_conf_file)
        omnium_state = PkgState(omnium, True)
        omnium_filename = os.path.join(metadata_dir, 'omnium_info.txt')
        with open(omnium_filename, 'w') as f:
            f.write('pkg_loc: {}\n'.format(omnium_state.location))
            f.write('conda_env: {}\n'.format(self._get_conda_env()))
            f.write('state: {}\n'.format(omnium_state))

        for pkg_name, pkg in self.analysis_pkgs.items():
            pkg_filename = os.path.join(metadata_dir, '{}_info.txt'.format(pkg_name))
            pkg_state = PkgState(pkg.pkg, True)
            with open(pkg_filename, 'w') as f:
                f.write('pkg_loc: {}\n'.format(os.path.dirname(pkg.pkg.__file__)))
                f.write('state: {}\n'.format(pkg_state))

        conda_list_filename = os.path.join(metadata_dir, 'conda_list.txt')
        try:
            # TODO: Happens on nosetest in PyCharm, because conda env not loaded.
            with open(conda_list_filename, 'w') as f:
                f.write(sp.check_output('conda list'.split()).decode())
        except FileNotFoundError:
            pass

        pip_freeze_filename = os.path.join(metadata_dir, 'pip_freeze.txt')
        try:
            with open(pip_freeze_filename, 'w') as f:
                f.write(sp.check_output('pip freeze'.split()).decode())
        except FileNotFoundError:
            pass

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

    def freeze(self):
        cmd = 'chmod -R u=rX {}'.format(self.suite_dir)
        logger.debug(cmd)
        logger.info('Suite frozen: no more commands can be run in suite')
        unfreeze_cmd = 'omnium suite-unfreeze {}'.format(self.suite_dir)
        logger.info('No dirs/files can be created/edited/deleted without running `{}`',
                    unfreeze_cmd)
        sp.call(cmd, shell=True)

    def unfreeze(self, suite_dir=None):
        if not suite_dir:
            suite_dir = self.suite_dir
        assert os.path.exists(suite_dir) and os.path.isdir(suite_dir)
        cmd = 'chmod -R u=rwX {}'.format(suite_dir)
        # N.B. logger is not hooked up to file.
        logger.debug(cmd)
        sp.call(cmd, shell=True)
        unfrozen_suite = Suite(suite_dir, False)
        assert not unfrozen_suite.is_readonly

        add_file_logging(unfrozen_suite.logging_filename)
        # Do once logger hooked up to file.
        logger.debug(cmd)
        logger.info('Unfrozen suite')

    def _get_conda_env(self):
        return os.environ.get('CONDA_DEFAULT_ENV')
