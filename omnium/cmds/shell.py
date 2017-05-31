"""Launches IPython shell"""
import os

ARGS = [(['--failsafe'], {'action': 'store_true'})]


def main(suite, args):
    import IPython

    if not args.failsafe:
        # Load up useful modules
        import iris
        import datetime as dt
        import numpy as np
        import pylab as plt

        import omnium as om
        from omnium.omnium_errors import OmniumError
        from omnium.stash import Stash
        from omnium.state import State
        from omnium.run_control import RunControl
        from omnium.converters import CONVERTERS
        from omnium.syncher import Syncher

        stash = Stash()
        state = State()

    # IPython.start_ipython(argv=[])
    # This is better because it allows you to access e.g. args, config.
    IPython.embed()
