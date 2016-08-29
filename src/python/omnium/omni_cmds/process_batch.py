"""Run processing"""
import os

from omnium.node_dag import get_node_dag
from omnium.processes import get_process_classes

ARGS = [(['batchname'], {'nargs': 1})]

def main(args, config):
    process_batch(args, config, args.batchname[0])


def process_batch(args, config, batchname):
    print('Processing batch {}'.format(batchname))
    dag = get_node_dag(args, config)
    process_classes = get_process_classes(args.cwd)

    batch = dag.get_batch(batchname)
    for to_group in batch.groups:
        for to_node in to_group.nodes:
            if to_node.status == 'done':
                print('Node {} already processed, skipping'.format(to_node))
                continue
            elif to_node.status == 'processing':
                raise Exception('Node {} currently being processed'.format(to_node))
            for from_node in to_node.from_nodes:
                if from_node.status != 'done':
                    raise Exception('Node {} does not exist'.format(from_node))

            process_class = process_classes[to_node.process]
            computer_name = open(config['computers']['current'], 'r').read().strip()
            process = process_class(args, config, computer_name)

            print('Processing {} with {}'.format(to_node, process.name))
            process.run(to_node)
            to_node.status = 'done'
            dag.commit()
            #dag.print_nodes()
            print('Processed {}'.format(to_node))
