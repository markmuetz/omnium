"""Launches IPython shell"""
ARGS = [(['--failsafe'], {'action': 'store_true'})]


def main(suite, args):
    import IPython

    if not args.failsafe:
        # Load up useful modules
        import os
        import datetime as dt
        import numpy as np
        import pylab as plt

        import iris

        import omnium as om
        from omnium.omnium_errors import OmniumError
        from omnium.stash import Stash
        from omnium.state import State
        from omnium.run_control import RunControl
        from omnium.converters import CONVERTERS
        from omnium.syncher import Syncher

        stash = Stash()
        state = State()

        for module in [os, dt, np, plt, iris, om]:
            print('Loaded module: {}'.format(module.__name__))

        for cls in [OmniumError, Stash, RunControl, Syncher]:
            print('Loaded class: {}'.format(cls.__name__))

        for name in CONVERTERS.keys():
            print('Loaded converter: {}'.format(name))

        for name, inst in [('stash', stash), ('state', state)]:
            print('Loaded instance: {}: {}'.format(name, inst))

    # IPython.start_ipython(argv=[])
    # This is better because it allows you to access e.g. args, config.
    IPython.embed()
