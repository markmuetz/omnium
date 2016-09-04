"""Launches IPython shell"""
import IPython

ARGS = [ (['--failsafe' ], {'action': 'store_true'}),
        ]

def main(args, config):
    if not args.failsafe:
        # Load up useful modules
        import iris
        import datetime as dt
        import pylab as plt
        import numpy as np
        from omnium.node_dag import get_node_dag
        from omnium.models import Base, Computer, Batch, Group, Node
        from omnium.processes import process_classes, proc_instance
        from omnium.stash import stash

        dag = get_node_dag(args, config)

    # IPython.start_ipython(argv=[])
    # This is better because it allows you to access e.g. args, config.
    IPython.embed()
