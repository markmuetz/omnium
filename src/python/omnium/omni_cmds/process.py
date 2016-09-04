"""Run processing"""
import os
from logging import getLogger

from omnium.node_dag import get_node_dag
from omnium.processes import process_classes

logger = getLogger('omni')

ARGS = [(['-b', '--batch'], {'help': 'Batch to process', 'nargs': '?'}),
        (['-g', '--group'], {'help': 'Group to process', 'nargs': '?'}),
        (['-n', '--node'], {'help': 'Node to process', 'nargs': '?'}),
        (['-a', '--all'], {'help': 'Process all nodes', 'action': 'store_true'}),
        (['-f', '--force'], {'help': 'Force processing for files that are already done',
                             'action': 'store_true',
                             'default': False}),
        ]

def main(args, config):
    dag = get_node_dag(args, config)

    if args.all:
        for batch in dag.get_batches():
            process_batch(args, config, dag, batch)
        return

    opts = [args.batch != None, args.group != None, args.node != None]
    if sum(opts) >= 2 or sum(opts) == 0:
        raise Exception('Please select exactly one of --batch, --group or --node')

    if args.batch:
        batch = dag.get_batch(args.batch)
        process_batch(args, config, dag, batch)
    elif args.group:
        group = dag.get_group(args.group)
        process_group(args, config, dag, group, 0)
    elif args.node:
        node = dag.get_node(args.node)
        process_node(args, config, dag, node, 0)


def process_batch(args, config, dag, batch):
    logger.info('Processing batch {}'.format(batch))
    for group in batch.groups:
        process_group(args, config, dag, group)
    batch.status = 'done'
    dag.commit()
    logger.info('Processed batch {}'.format(batch))


def process_group(args, config, dag, group, indent=1):
    logger.info('  '*indent + 'Processing group {}'.format(group))
    for node in group.nodes:
        process_node(args, config, dag, node, indent+1)
    group.status = 'done'
    dag.commit()
    logger.info('  '*indent + 'Processed group {}'.format(group))


def process_node(args, config, dag, node, indent=2):
    logger.info('  '*indent + 'Processing node {}'.format(node))
    if not args.force and node.status == 'done':
        logger.info('  '*(indent + 1) + 'Node {} already processed, skipping'.format(node))
        return
    elif node.status == 'processing':
        raise Exception('Node {} currently being processed'.format(node))
    for from_node in node.from_nodes:
        if from_node.status != 'done':
            raise Exception('Node {} does not exist'.format(from_node))

    if node.process == None:
        raise Exception('Node {} does not not have a process\n(is it an init node?)'.format(node))

    logger.info('  '*(indent+1) + 'Using process {}'.format(node.process))
    process_class = process_classes[node.process]
    process = process_class(args, config, node)

    process.load()
    process.run()
    process.save()
    process.done()

    dag.commit()
    logger.info('  '*indent + 'Processed {}'.format(node))
