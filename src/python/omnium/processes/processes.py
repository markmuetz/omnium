class Process(object):
    name = None
    def __init__(self, args, config, node):
        self.args = args
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

    def load(self):
        pass

    def run(self):
        if not self.data:
            raise Exception('No data has been loaded yet for {}'.format(self))

    def save(self):
        if not self.processed_data:
            raise Exception('No processed data has been made yet for {}'.format(self))

    def done(self):
        if not self.processed_data:
            raise Exception('Processed data has been saved yet for {}'.format(self))
        filename = self.node.filename(self.config)
        with open(filename + '.done', 'w') as f:
            f.write(self.comments)
        self.node.status = 'done'
        return filename + '.done'

    def __str__(self):
        return '<Process {} for Node {}>'.format(self.name, self.node.name)

    def __repr__(self):
        return '<Process {} for Node {}>'.format(self.name, self.node.__repr__())


