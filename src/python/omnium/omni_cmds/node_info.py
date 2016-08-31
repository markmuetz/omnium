"""Print info about a given file"""
import os
from glob import glob

import iris

from omnium.node_dag import get_node_dag
from omnium.models import Node

ARGS = [(['node_ids'], {'help': 'ID of node to get info for', 
                        'nargs': '+'}),
        ]

def main(args, config):
    dag = get_node_dag(args, config)
    for node_id in args.node_ids:
	node = dag._session.query(Node).filter_by(id=node_id).one()
	print(node)
	print(node.filename(dag.computer_name, config))
	print('')
