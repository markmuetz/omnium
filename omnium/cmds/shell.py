"""Launches IPython shell"""
import os

ARGS = [(['--failsafe'], {'action': 'store_true'})]


def main(args):
    import IPython

    if not args.failsafe:
        # Load up useful modules
        import iris
        import datetime as dt
        import numpy as np

        import omnium as om
        from omnium.omnium_errors import OmniumError
        from omnium.stash import Stash
        from omnium.state import State
        from omnium.suite import Suite
        from omnium.run_control import RunControl
        from omnium.converters import CONVERTERS
        from omnium.syncher import Syncher

        stash = Stash()
        state = State()
        suite = Suite()
        try:
            suite.load(os.getcwd())
        except OmniumError:
            print('NOT IN A SUITE')
            print('')

        import pylab as plt
    # IPython.start_ipython(argv=[])
    # This is better because it allows you to access e.g. args, config.
    IPython.embed()
