ARGS = [(['--analysis', '-a'], {'help': 'Analysis to run'}),
        (['--data-type', '-d'], {'help': 'datam/[dataw]', 'default': 'datam'}),
        (['expt'], {'nargs': 1, 'help': 'Experiment to analyze'}),
        (['--all'], {'help': 'Run all analysis', 'action': 'store_true'}),
        (['--force', '-f'], {'help': 'Force run', 'action': 'store_true'})]


def main(args):
    from omnium.run_control import RunControl
    run_control = RunControl(args.data_type, args.expt[0], args.force)
    run_control.setup()
    run_control.check_setup()
    run_control.gen_analysis_workflow()

    if args.all:
        run_control.run_all()
    elif args.analysis:
        run_control.run_analysis(args.analysis)
