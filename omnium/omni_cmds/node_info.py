"""Print info about a given file"""
import os
from glob import glob
ARGS = [(['node_names'], {'help': 'Name(s) of node to get info for',
                          'nargs': '+'})]


def print_node_info(node, config):
    print(node.group.batch)
    print('  ' + node.group.__str__())
    print('    ' + node.__str__())
    print('    ' + node.filename(config))
    print('    ' + '<history>')
    if node.status == 'done':
        with open(node.filename(config) + '.done', 'r') as infile:
            for line in infile.readlines():
                print('    ' + line)
    print('')


def main(args, config, process_classes):
    from sqlalchemy.orm.exc import NoResultFound

    from omnium.node_dag import NodeDAG
    from omnium.models import Node

    dag = NodeDAG(config, process_classes)
    for node_name in args.node_names:
        nodes = dag.get_nodes(node_name)
        if len(nodes):
            for node in nodes:
                print_node_info(node, config)
        else:
            print('No node with name {}'.format(node_name))
