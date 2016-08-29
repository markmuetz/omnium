"""Print all nodes grouped by batch, group"""
from omnium.node_dag import get_node_dag

ARGS = [(['--computer'], {'nargs': '?'})]

def main(args, config):
    if args.computer:
        dag = get_node_dag(args, config, args.computer)
    else:
        dag = get_node_dag(args, config)
    dag.print_nodes()
