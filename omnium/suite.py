import os
from omnium_errors import OmniumError

class Suite(object):
    def __init__(self):
        self.name = None
        self.suite_dir = None
        self.is_in_suite = False
        self.is_omnium_app = False
        self.is_omnium_analysis = False

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


    def info(self):
        with open(os.path.join(self.suite_dir, 'rose-suite.info'), 'r') as f:
            return f.read()
