import importlib
from logging import getLogger

from models import Node
logger = getLogger('omni')


class ProcessEngine(object):
    def __init__(self, force, config, process_classes, dag):
        self.force = force
        self.config = config
        self.process_classes = process_classes
        self.dag = dag

    def process_batch(self, batch):
        logger.info('Processing batch {}'.format(batch))
        for group in batch.groups:
            self.process_group(group, verify=False)
        self.dag.verify_status(update=True)
        logger.info('Processed batch {}'.format(batch))

    def process_group(self, group, indent=1, verify=True):
        logger.info('  '*indent + 'Processing group {}'.format(group))
        for node in group.nodes:
            self.process_node(node, indent+1, verify=False)
        if verify:
            self.dag.verify_status(update=True)
        logger.info('  '*indent + 'Processed group {}'.format(group))

    def process_node(self, node, indent=2, verify=True):
        logger.info('  '*indent + 'Processing node {}'.format(node))
        if not self.force and node.status == 'done':
            logger.info('  '*(indent + 1) + 'Node {} already processed, skipping'.format(node))
            return
        elif node.status == 'processing':
            raise Exception('Node {} currently being processed'.format(node))

        if not node.from_nodes:
            logger.info('  '*(indent + 1) + 'Node {} has no from nodes, skipping'.format(node))
            return
        for from_node in node.from_nodes:
            if from_node.status != 'done':
                raise Exception('Node {} does not exist'.format(from_node))

        if node.process is None:
            raise Exception('Node {} does not not have a process\n(is it an init node?)'
                            .format(node))

        logger.info('  '*(indent+1) + 'Using process {}'.format(node.process))
        process_class = self.process_classes[node.process]
        process = process_class(self.config, node)

        process.load_modules()
        process.load_upstream()
        process.run()
        process.save()
        process.done()

        if verify:
            self.dag.verify_status(update=True)
        logger.info('  '*indent + 'Processed {}'.format(node))

    def load(self, node):
        if not node or not isinstance(node, Node):
            raise Exception('Node must be set')

        if node.status != 'done':
            raise Exception('Node data has not been processed yet')

        ntype = node.node_type()
        if ntype in ['fields_file', 'netcdf']:
            logger.debug('Loading {} node: {}'.format(node, ntype))
            iris = importlib.import_module('iris')
            return iris.load(node.filename(self.config))
        elif ntype == 'png':
            raise Exception('Cannot load png')
        else:
            raise Exception('Unknown node type {}'.format(ntype))
