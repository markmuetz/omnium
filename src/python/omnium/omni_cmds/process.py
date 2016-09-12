"""Run processing"""
import os
from logging import getLogger

logger = getLogger('omni')

ARGS = [(['-b', '--batch'], {'help': 'Batch to process', 'nargs': '?'}),
        (['-g', '--group'], {'help': 'Group to process', 'nargs': '?'}),
        (['-n', '--node'], {'help': 'Node to process', 'nargs': '?'}),
        (['-a', '--all'], {'help': 'Process all nodes', 'action': 'store_true'}),
        (['-f', '--force'], {'help': 'Force processing for files that are already done',
                             'action': 'store_true',
                             'default': False})]


def main(args, config, process_classes):
    from omnium.node_dag import NodeDAG
    from omnium.process_engine import ProcessEngine

    dag = NodeDAG(config, process_classes)
    proc_eng = ProcessEngine(args.force, config, process_classes, dag)

    if args.all:
        for batch in dag.get_batches():
            proc_eng.process_batch(batch)
        return

    opts = [args.batch is not None, args.group is not None, args.node is not None]
    if sum(opts) >= 2 or sum(opts) == 0:
        raise Exception('Please select exactly one of --batch, --group or --node')

    if args.batch:
        batch = dag.get_batch(args.batch)
        proc_eng.process_batch(batch)
    elif args.group:
        group = dag.get_group(args.group)
        proc_eng.process_group(group, 0)
    elif args.node:
        node = dag.get_node(args.node)
        proc_eng.process_node(node, 0)
