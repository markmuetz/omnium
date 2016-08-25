"""Launches IPython shell"""
import IPython

ARGS = [(['--dag'], {'action': 'store_true'}),
        (['--models'], {'action': 'store_true'}),
        ]

def main(args, config):
    if args.dag:
        from omnium.node_dag import get_node_dag
        dag = get_node_dag(args, config)
    if args.models:
        from omnium.models import Base, Computer, Batch, Group, Node
    # IPython.start_ipython(argv=[])
    # This is better because it allows you to access e.g. args, config.
    IPython.embed()
