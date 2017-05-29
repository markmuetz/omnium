import os
import io
from collections import OrderedDict
from logging import getLogger
from configparser import ConfigParser

from omnium.analyzers import get_analysis_classes
from omnium_errors import OmniumError
from utils import get_git_info

logger = getLogger('omnium')


class Suite(object):
    suite_types = ['runcontrol', 'run', 'archive', 'mirror']

    def __init__(self):
        self.name = None
        self.suite_dir = None
        self.is_in_suite = False
        self.is_omnium_app = False
        self.is_init = False
        self.local_analyzers_dir = None
        self.central_analyzers_dir = None
        self.analysis_classes = OrderedDict()

    def load(self, cwd):
        suite_dir = cwd
        while not os.path.exists(os.path.join(suite_dir, 'rose-suite.info')):
            suite_dir = os.path.dirname(suite_dir)
            if os.path.dirname(suite_dir) == suite_dir:
                # at root dir: /
                raise OmniumError('No rose-suite.info found - not in a suite?')
        self.is_in_suite = True
        self.suite_dir = suite_dir
        self.name = os.path.basename(suite_dir)
        logger.debug('in suite: {}'.format(self.suite_dir))

        # Check to see if it's already been initialized.
        config_filename = os.path.join(self.suite_dir, '.omnium/suite.conf')
        if os.path.exists(config_filename):
            self.is_init = True
            self.suite_config = ConfigParser()
            with open(config_filename, 'r') as f:
                self.suite_config.read_file(f)
            logger.debug('loaded suite config')

        # Check for omnium app.
        if os.path.exists(os.path.join(self.suite_dir, 'app/omnium/rose-app.conf')):
            self.is_omnium_app = True
            self.app_config_path = os.path.join(self.suite_dir, 'app/omnium/rose-app.conf')
            self.app_config = ConfigParser()
            with open(self.app_config_path, 'r') as f:
                self.app_config.read_file(f)
            # I have an app config. See if I can find central_analysis_classes:
            if 'OMNIUM_ANALYZERS_DIR' in self.app_config['env']:
                self.central_analyzers_dir = self.app_config['env']['OMNIUM_ANALYZERS_DIR']
            logger.debug('loaded app config')

        # Check for local analyzers.
        if os.path.exists(os.path.join(self.suite_dir, 'app/omnium/analysis')):
            self.local_analyzers_dir = os.path.join(self.suite_dir, 'app/omnium/')

        if self.local_analyzers_dir or self.central_analyzers_dir:
            # Load these first, these take precedence over centralized ones.
            if self.local_analyzers_dir:
                logger.debug('loading local analyzers')
                self.analysis_classes = get_analysis_classes(self.local_analyzers_dir)

            if self.central_analyzers_dir:
                logger.debug('loading central analyzers')
                git_hash, git_status = get_git_info(self.central_analyzers_dir)
                logger.debug('analyzers git_hash, status: {}, {}'.format(git_hash, git_status))
                central_analysis_classes = get_analysis_classes(self.central_analyzers_dir)
                self.central_analysis_hash = git_hash
                self.central_analysis_status = git_status
                # Add any analyzers *not already in classes*.
                for k, v in central_analysis_classes.items():
                    if k not in self.analysis_classes:
                        self.analysis_classes[k] = v

    def init(self, suite_type, host=None):
        assert suite_type in Suite.suite_types
        logger.info('Initializing suite, type: {}'.format(suite_type))
        logger.debug('Creating in {}'.format(self.suite_dir))
        self.load(self.suite_dir)

        suite_config = ConfigParser()
        suite_config.add_section('settings')
        suite_config.set('settings', 'suite_type', suite_type)

        if suite_type == 'mirror':
            suite_config.add_section('remote')
            suite_config.set('remote', 'host', host)

        dotomnium_dir = os.path.join(self.suite_dir, '.omnium')
        os.makedirs(dotomnium_dir)
        with open(os.path.join(dotomnium_dir, 'suite.conf'), 'wb') as configfile:
            suite_config.write(configfile)
        self.load(self.suite_dir)

    def suite_config_lines(self):
        conf_text = io.StringIO()
        self.suite_config.write(conf_text)
        conf_text.seek(0)
        return [l[:-1] for l in conf_text.readlines()]

    def info_lines(self):
        with open(os.path.join(self.suite_dir, 'rose-suite.info'), 'r') as f:
            return [l[:-1] for l in f.readlines()]
