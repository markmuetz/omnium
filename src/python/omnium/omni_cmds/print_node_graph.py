"""Print all nodes grouped by batch, group"""
from omnium.node_dag import NodeDAG

ARGS = [(['--computer'], {'nargs': '?'})]


def main(args, config):
    if args.computer:
        dag = NodeDAG(config, args.computer)
    else:
        dag = NodeDAG(config)
    dag.print_nodes()
