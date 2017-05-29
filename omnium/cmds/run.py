ARGS = [(['--analysis', '-a'], {'help': 'Analysis to run'}),
        (['--run-type', '-d'], {'help': 'cycle/expt/[suite]', 'default': 'suite'}),
        (['expts'], {'nargs': '*', 'help': 'Experiment to analyze'}),
        (['--all'], {'help': 'Run all analysis', 'action': 'store_true'}),
        (['--filenames', '-n'], {'help': 'Filenames to run on'}),
        (['--force', '-f'], {'help': 'Force run', 'action': 'store_true'}),
        (['--interactive', '-i'], {'help': 'Run interactively', 'action': 'store_true'})]


def main(args):
    from omnium.run_control import RunControl
    run_control = RunControl(args.run_type, args.expts, args.force, args.interactive)
    run_control.gen_analysis_workflow()

    if args.all:
        run_control.run_all()
    elif args.analysis:
        run_control.run_analysis(args.analysis, args.filenames)
