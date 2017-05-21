ARGS = [(['--analysis', '-a'], {'help': 'Analysis to run'}),
        (['--run-type', '-d'], {'help': '[cycle]/expt/suite', 'default': 'cycle'}),
        (['expts'], {'nargs': '*', 'help': 'Experiment to analyze'}),
        (['--all'], {'help': 'Run all analysis', 'action': 'store_true'}),
        (['--force', '-f'], {'help': 'Force run', 'action': 'store_true'})]


def main(args):
    from omnium.run_control import RunControl
    run_control = RunControl(args.run_type, args.expts, args.force)
    run_control.setup()
    run_control.check_setup()
    run_control.gen_analysis_workflow()

    if args.all:
        run_control.run_all()
    elif args.analysis:
        run_control.run_analysis(args.analysis)
