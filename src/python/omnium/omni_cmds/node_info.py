"""Print info about a given file"""
import os
from glob import glob
ARGS = [(['node_names'], {'help': 'Name(s) of node to get info for',
                          'nargs': '+'})]


def main(args, config, process_classes):
    from sqlalchemy.orm.exc import NoResultFound

    from node_dag import NodeDAG
    from models import Node

    dag = NodeDAG(config, process_classes)
    for node_name in args.node_names:
        try:
            node = dag.get_node(node_name)
            print(node)
            print(node.filename(config))
            print('')
        except NoResultFound:
            print('No node with name {}'.format(node_name))
