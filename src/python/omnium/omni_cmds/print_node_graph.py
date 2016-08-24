"""Print all nodes grouped by batch, group"""
from omnium.node_dag import get_node_dag

ARGS = []

def main(args, config):
    dag = get_node_dag(args, config)
    dag.print_nodes()
