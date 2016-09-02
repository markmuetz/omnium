"""Launches IPython shell"""
import IPython

ARGS = [(['--dag'], {'action': 'store_true'}),
        (['--models'], {'action': 'store_true'}),
        (['-u', '--useful'], {'action': 'store_true'}),
        ]

def main(args, config):
    if args.dag or args.useful:
        from omnium.node_dag import get_node_dag
        dag = get_node_dag(args, config)
    if args.models or args.useful:
        from omnium.models import Base, Computer, Batch, Group, Node
    if args.useful:
        import iris
        import datetime as dt
        import pylab as plt
        import numpy as np
        from omnium.processes import process_classes, proc_instance
        from omnium.stash import stash
    # IPython.start_ipython(argv=[])
    # This is better because it allows you to access e.g. args, config.
    IPython.embed()
