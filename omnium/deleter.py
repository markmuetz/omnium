import os
from logging import getLogger

from omnium.analyser import Analyser

logger = getLogger('om.deleter')


class Deleter(Analyser):
    analysis_name = 'deleter'
    def load(self):
        pass

    def run_analysis(self):
        pass

    def save(self, state=None, suite=None):
        if not (self.min_runid <= self.get_runid(self.filename) <= self.max_runid):
            logger.debug('file {} out of runid range: {} - {}'.format(self.filename,
                                                                      self.min_runid,
                                                                      self.max_runid))
            return

        self.messages = ['archer_analysis delete ' + self.analysis_name]
        logger.info('Delete: {}'.format(self.filename))
        os.remove(self.filename)
        self.messages.append('Deleted original')

        with open(self.filename + '.deleted', 'w') as f:
            f.write('\n'.join(self.messages))
            f.write('\n')
