import os
from logging import getLogger

logger = getLogger('omni')


class Process(object):
    name = None

    def __init__(self, config, node):
        self.config = config
        self.node = node
        self.comments = ''
        self.data = None
        self.processed_data = None
        self.saved = False

        if self.name in self.config['process_options']:
            self.options = self.config['process_options'][self.name]
        else:
            self.options = {}

    def load_modules(self):
        pass

    def load_upstream(self):
        logger.debug('loading {}'.format(self.node))
        for from_node in self.node.from_nodes:
            if not from_node.status == 'done':
                logger.error('Node: {}'.format(self.node))
                logger.error('From node not done: {}'.format(from_node))
                raise Exception('Not all from nodes have been processed')

    def run(self):
        logger.debug('running {}'.format(self.node))
        if not self.data:
            raise Exception('No data has been loaded yet for {}'.format(self))

    def save(self):
        logger.debug('saving {}'.format(self.node))
        if not self.processed_data:
            raise Exception('No processed data has been made yet for {}'.format(self))
        dirname = os.path.dirname(self.node.filename(self.config))
        if not os.path.exists(dirname):
            logger.debug('Creating dir {}'.format(dirname))
            os.makedirs(dirname)

    def done(self):
        if not self.processed_data:
            raise Exception('Processed data has been saved yet for {}'.format(self))
        filename = self.node.filename(self.config)
        with open(filename + '.done', 'w') as f:
            f.write(self.comments)
        self.node.status = 'done'
        logger.debug('finished {}'.format(self.node))
        return filename + '.done'

    def __str__(self):
        return '<Process {} for Node {}>'.format(self.name, self.node.name)

    def __repr__(self):
        return '<Process {} for Node {}>'.format(self.name, self.node.__repr__())
