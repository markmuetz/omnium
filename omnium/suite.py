import os
import io
from logging import getLogger
from configparser import ConfigParser

from omnium_errors import OmniumError

logger = getLogger('omnium')


class Suite(object):
    suite_types = ['runcontrol', 'run', 'archive', 'mirror']

    def __init__(self):
        self.name = None
        self.suite_dir = None
        self.is_in_suite = False
        self.is_omnium_app = False
        self.is_omnium_analysis = False
        self.is_init = False

    def check_in_suite_dir(self, cwd):
        suite_dir = cwd
        while not os.path.exists(os.path.join(suite_dir, 'rose-suite.info')):
            suite_dir = os.path.dirname(suite_dir)
            if os.path.dirname(suite_dir) == suite_dir:
                # at root dir: /
                raise OmniumError('No rose-suite.info found - not in a suite?')
        self.is_in_suite = True
        self.suite_dir = suite_dir
        self.name = os.path.basename(suite_dir)

        # Check for omnium app.
        if os.path.exists(os.path.join(self.suite_dir, 'app/omnium/rose-app.conf')):
            self.is_omnium_app = True
            self.omnium_app_conf = os.path.join(self.suite_dir, 'app/omnium/rose-app.conf')

        # Check for omnium analysis.
        if os.path.exists(os.path.join(self.suite_dir, 'app/omnium/file/analysis')):
            self.is_omnium_analysis = True
            self.omnium_analysis_dir = os.path.join(self.suite_dir, 'app/omnium/file/')

        # Check to see if it's already been initialized.
        config_filename = os.path.join(self.suite_dir, '.omnium/suite.conf')
        if os.path.exists(config_filename):
            self.is_init = True
            self.config = ConfigParser()
            with open(config_filename, 'r') as f:
                self.config.read_file(f)

    def init(self, suite_type, host=None):
        assert suite_type in Suite.suite_types
        logger.info('Initializing suite, type: {}'.format(suite_type))
        logger.debug('Creating in {}'.format(self.suite_dir))
        self.check_in_suite_dir(self.suite_dir)

        config = ConfigParser()
        config.add_section('settings')
        config.set('settings', 'suite_type', suite_type)

        if suite_type == 'mirror':
            config.add_section('remote')
            config.set('remote', 'host', host)

        dotomnium_dir = os.path.join(self.suite_dir, '.omnium')
        os.makedirs(dotomnium_dir)
        with open(os.path.join(dotomnium_dir, 'suite.conf'), 'wb') as configfile:
            config.write(configfile)
        self.check_in_suite_dir(self.suite_dir)

    def config_lines(self):
        conf_text = io.StringIO()
        self.config.write(conf_text)
        conf_text.seek(0)
        return [l[:-1] for l in conf_text.readlines()]

    def info_lines(self):
        with open(os.path.join(self.suite_dir, 'rose-suite.info'), 'r') as f:
            return [l[:-1] for l in f.readlines()]
