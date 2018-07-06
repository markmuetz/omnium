"""Launches IPython shell"""
ARGS = [(['--failsafe'], {'action': 'store_true'})]
RUN_OUTSIDE_SUITE = True


def main(suite, args):
    import IPython

    if not args.failsafe:
        # Load up useful modules
        import os
        import datetime as dt
        import numpy as np

        import iris

        import omnium as om
        from omnium.omnium_errors import OmniumError
        from omnium.stash import Stash
        from omnium.state import State
        from omnium.run_control import RunControl
        from omnium.converter import FF2NC_Converter
        from omnium.syncher import Syncher

        stash = Stash()
        state = State()

        modules = [os, dt, np, iris, om]
        try:
            import pylab as plt
            modules.append(plt)
        except ImportError:
            pass
        for module in modules:
            print('Loaded module: {}'.format(module.__name__))

        for cls in [OmniumError, Stash, RunControl, Syncher, FF2NC_Converter]:
            print('Loaded class: {}'.format(cls.__name__))

        print('Loaded instance: {}: {}'.format('state', state))
        len_stash_entries = sum([len(od) for od in stash.values()])
        print('Loaded instance: {}: {} entries'.format('stash', len_stash_entries))

    # IPython.start_ipython(argv=[])
    # This is better because it allows you to access e.g. args, config.
    IPython.embed()
