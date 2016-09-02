"""Print info about a given file"""
import os
from glob import glob
from sqlalchemy.orm.exc import NoResultFound

import iris

from omnium.node_dag import get_node_dag
from omnium.models import Node

ARGS = [(['node_names'], {'help': 'Name(s) of node to get info for', 
                         'nargs': '+'}),
        ]

def main(args, config):
    dag = get_node_dag(args, config)
    for node_name in args.node_names:
        try:
            node = dag.get_node(node_name)
            print(node)
            print(node.filename(config))
            print('')
        except NoResultFound:
            print('No node with name {}'.format(node_name))
