"""Launches IPython shell"""
ARGS = [(['--failsafe'], {'action': 'store_true'})]
RUN_OUTSIDE_SUITE = True


def main(cmd_ctx, args):
    import IPython
    import os
    import datetime as dt

    if not args.failsafe:
        # Load up useful modules
        import numpy as np

        import iris

        import omnium as om
        from omnium.omnium_errors import OmniumError
        from omnium.stash import Stash
        from omnium.pkg_state import PkgState
        from omnium.suite import ExptList
        from omnium.run_control import RunControl, TaskMaster
        from omnium.analysis.converter import FF2NC_Converter
        from omnium.syncher import Syncher

        stash = Stash()
        omnium_state = PkgState(om)

        modules = [os, dt, np, iris]
        try:
            import pylab as plt
            modules.append(plt)
        except ImportError:
            pass
        for module in modules:
            print('Loaded module: {}'.format(module.__name__))
        print('Loaded module: omnium as om')

        for cls in [OmniumError, Stash, RunControl, Syncher, FF2NC_Converter,
                    ExptList, TaskMaster]:
            print('Loaded class: {}'.format(cls.__name__))

        suite = cmd_ctx.suite
        analysis_pkgs = cmd_ctx.analysis_pkgs
        print('Loaded instance: {}: {}'.format('suite', repr(suite)))
        print('Loaded instance: {}: {}'.format('analysis_pkgs', repr(analysis_pkgs)))
        print('Loaded instance: {}: {}'.format('omnium_state', omnium_state))
        len_stash_entries = sum([len(od) for od in stash.values()])
        print('Loaded instance: {}: {} entries'.format('stash', len_stash_entries))

        if suite.is_in_suite:
            print('In suite:')
            try:
                syncher = Syncher(suite)
            except:
                syncher = None
            expts = suite.expts
            cmd_run_control = RunControl(suite, 'cmd', [e.name for e in expts], 'test')
            cycle_run_control = RunControl(suite, 'cycle', [e.name for e in expts], 'test')
            expt_run_control = RunControl(suite, 'expt', [e.name for e in expts], 'test')
            suite_run_control = RunControl(suite, 'suite', [e.name for e in expts], 'test')
            for rc in [cmd_run_control, cycle_run_control, expt_run_control, suite_run_control]:
                rc.gen_analysis_workflow()
            print('  Loaded suite instance: {}: {}'.format('syncher', syncher))
            print('  Loaded suite instance: {}: {}'.format('expts', expts))
            print('  Loaded suite instance: {}: {}'.format('cmd_run_control', cmd_run_control))
            print('  Loaded suite instance: {}: {}'.format('cycle_run_control', cycle_run_control))
            print('  Loaded suite instance: {}: {}'.format('expt_run_control', expt_run_control))
            print('  Loaded suite instance: {}: {}'.format('suite_run_control', suite_run_control))

    # IPython.start_ipython(argv=[])
    # This is better because it allows you to access e.g. args, config.
    IPython.embed()
