import os
from logging import getLogger

from omnium.analyser import Analyser

logger = getLogger('om.deleter')


class Deleter(Analyser):
    analysis_name = 'deleter'
    single_file = True

    def load(self):
        pass

    def run_analysis(self):
        pass

    def save(self, state=None, suite=None):
        self.messages = ['archer_analysis delete ' + self.analysis_name]
        logger.info('Delete: {}', self.filename)
        os.remove(self.filename)
        self.messages.append('Deleted original')

        with open(self.filename + '.deleted', 'w') as f:
            f.write('\n'.join(self.messages))
            f.write('\n')
