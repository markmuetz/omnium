"""Launches IPython shell"""
ARGS = [(['--failsafe'], {'action': 'store_true'})]


def main(args, config, process_classes):
    import IPython

    if not args.failsafe:
        # Load up useful modules
        import iris
        import datetime as dt
        import pylab as plt
        import numpy as np
        from omnium.node_dag import NodeDAG
        from omnium.models import Base, Computer, Batch, Group, Node
        from omnium.processes import process_classes, proc_instance
        from omnium.stash import stash
        from omnium.process_engine import ProcessEngine
        if 'remote' in config['computers'][config['computer_name']]:
            from omnium.syncher import Syncher
            syncher = Syncher(False, config)

        dag = NodeDAG(config, process_classes)
        proc_eng = ProcessEngine(False, config, process_engine, dag)

    # IPython.start_ipython(argv=[])
    # This is better because it allows you to access e.g. args, config.
    IPython.embed()
