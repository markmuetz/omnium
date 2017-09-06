import os

ARGS = [(['--analysis', '-a'], {'help': 'Analysis to run'}),
        (['--run-type', '-t'], {'help': 'cycle/expt/[suite]', 'default': 'suite'}),
        (['expts'], {'nargs': '+', 'help': 'Experiment to analyse'}),
        (['--all'], {'help': 'Run all analysis', 'action': 'store_true'}),
        (['--filenames', '-n'], {'help': 'Filenames to run on'}),
        (['--force', '-f'], {'help': 'Force run', 'action': 'store_true'}),
        (['--production', '-p'], {'help': 'Run in production mode', 'action': 'store_true'}),
        (['--mpi'], {'help': 'Run using mpi', 'action': 'store_true'}),
        (['--display-only', '-d'], {'help': 'Display only (must have been run previously)',
                                    'action': 'store_true'}),
        (['--interactive', '-i'], {'help': 'Run interactively', 'action': 'store_true'})]


def get_logging_filename(suite, args):
    if args.run_type in ['cycle', 'expt']:
        assert len(args.expts) == 1
        expt = args.expts[0] + '_'
    else:
        expt = ''

    if args.mpi:
        # Note this will raise an import error if not installed.
        import mpi4py
        comm = mpi4py.MPI.COMM_WORLD
        rank = str(comm.Get_rank()) + '_'
    else:
        rank = ''

    filename = os.path.basename(suite.logging_filename)
    dirname = os.path.dirname(suite.logging_filename)
    return os.path.join(dirname, expt + rank + filename)


def main(suite, args):
    from omnium.run_control import RunControl
    production = (os.getenv('PRODUCTION') == 'True') or args.production
    run_control = RunControl(suite, args.run_type, args.expts, production, args.force,
                             args.display_only, args.interactive)
    run_control.gen_analysis_workflow()

    if args.all:
        run_control.run_all()
    elif args.analysis:
        run_control.run_analysis(args.analysis, args.filenames)
