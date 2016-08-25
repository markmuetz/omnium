"""Print all nodes grouped by batch, group"""
from omnium.node_dag import regenerate_node_dag, generate_node_dag

ARGS = [(['--disable-print'], {'help': 'Disable printing of graph',
                               'action': 'store_true',
                               'default': False}),
         (['--regen'], {'help': 'Regenerate node graph from scratch',
                               'action': 'store_true',
                               'default': False}),
                               ]

def main(args, config):
    if args.regen:
        dag = regenerate_node_dag(args, config)
    else:
        dag = generate_node_dag(args, config)

    if not args.disable_print:
        dag.print_nodes()
