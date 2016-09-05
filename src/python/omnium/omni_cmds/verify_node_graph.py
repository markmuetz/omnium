"""Print all nodes grouped by batch, group"""
from omnium.node_dag import NodeDAG

ARGS = [(['--update'], {'action': 'store_true'})]

def main(args, config):
    dag = NodeDAG(config)
    dag.verify_status(args.update)
