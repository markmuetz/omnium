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
            suite.check_in_suite_dir(os.getcwd())
        except OmniumError:
            print('NOT IN A SUITE')
            print('')

        if suite.is_in_suite:
            from omnium.analyzers import get_analysis_classes
            syncher = Syncher(suite)
            analysis_classes = get_analysis_classes(suite.omnium_analysis_dir)
        import pylab as plt
    # IPython.start_ipython(argv=[])
    # This is better because it allows you to access e.g. args, config.
    IPython.embed()
