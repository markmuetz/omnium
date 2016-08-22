"""Run processing"""
import os

from omnium.node_dag import create_node_dag
from omnium.processes import get_process_classes

ARGS = [(['batchname'], {'nargs': 1})]

def main(args, config):
    process_batch(args, config, args.batchname[0])


def process_batch(args, config, batchname):
    print('Processing batch {}'.format(batchname))
    dag = create_node_dag(args, config)
    process_classes = get_process_classes(args.cwd)

    to_groups = dag.batches[batchname]
    for to_group in to_groups:
        for to_node in to_group.nodes:
            if to_node.exists():
                print('Node {} already exists, skipping'.format(to_node))
                continue
            
            for from_node in to_node.from_nodes:
                if not from_node.exists():
                    raise Exception('Node {} does not exist'.format(from_node))

            process_class = process_classes[to_node.process_name]
            process = process_class()

            print('Processing {} with {}'.format(to_node, process.name))
            process.run(to_node)
            print('Processed {}'.format(to_node))
