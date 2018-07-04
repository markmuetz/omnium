"""Runs specified analysis on files"""
import os
from logging import getLogger

from omnium.omnium_errors import OmniumError

logger = getLogger('om.run')

ARGS = [(['--analysis', '-a'], {'help': 'Analysis to run'}),
        (['--run-type', '-t'], {'help': 'cycle/expt/suite/[cmd]', 'default': 'cmd'}),
        (['expts'], {'nargs': '*', 'help': 'Experiments to analyse'}),
        (['--all'], {'help': 'Run all analysis', 'action': 'store_true'}),
        (['--filenames', '-n'], {'nargs': '+', 'help': 'Filenames to run on'}),
        (['--force', '-f'], {'help': 'Force run', 'action': 'store_true'}),
        (['--production', '-p'], {'help': 'Run in production mode', 'action': 'store_true'}),
        (['--print-only', '-o'], {'help': 'Print only', 'action': 'store_true'}),
        (['--no-run-if-started'], {'help': 'Only run if no outfile log',
                                   'action': 'store_true'}),
        (['--settings', '-s'], {'help': 'Settings to use',
                                'default': 'default'}),
        (['--mpi'], {'help': 'Run using mpi', 'action': 'store_true'})]


def get_logging_filename(suite, args):
    if args.run_type in ['cycle', 'expt']:
        expt = '_'.join(args.expts) + '_'
    else:
        expt = ''

    if args.mpi:
        # Note this will raise an import error if not installed.
        from mpi4py import MPI
        comm = MPI.COMM_WORLD
        rank = 'mpi_rank_' + str(comm.Get_rank()) + '_'
    else:
        rank = ''

    filename = os.path.basename(suite.logging_filename)
    dirname = os.path.dirname(suite.logging_filename)
    return os.path.join(dirname, expt + rank + filename)


def main(suite, args):
    from omnium.run_control import RunControl
    production = (os.getenv('PRODUCTION') == 'True') or args.production
    if args.filenames:
        assert args.run_type == 'cmd'
        expts = []
        for fn in args.filenames:
            absfn = os.path.abspath(fn)
            if not os.path.exists(absfn):
                raise OmniumError('{} not found'.format(absfn))
            expt = os.path.basename(os.path.dirname(absfn))
            if expt not in expts:
                expts.append(expt)
    else:
        expts = args.expts

    run_control = RunControl(suite, args.run_type, expts, args.settings, production,
                             args.force, args.no_run_if_started)
    if args.mpi:
        # Note this will raise an import error if not installed.
        from mpi4py import MPI
        from omnium.mpi_control import MpiMaster, MpiSlave
        comm = MPI.COMM_WORLD
        rank = comm.Get_rank()
        size = comm.Get_size()
        logger.debug('Size, rank: {}, {}', size, rank)
        run_control.gen_analysis_workflow()
        if rank == 0:
            run_control.gen_tasks()
            master = MpiMaster(run_control, comm, rank, size)
            master.run()
        else:
            slave = MpiSlave(run_control, comm, rank, size)
            slave.listen()
    else:
        run_control.gen_analysis_workflow()

        if args.all:
            run_control.gen_tasks()
            if args.print_only:
                run_control.print_tasks()
            else:
                run_control.run_all()
        elif args.analysis:
            run_control.gen_tasks_for_analysis(args.analysis, args.filenames)
            if args.print_only:
                run_control.print_tasks()
            else:
                run_control.run_single_analysis(args.analysis)
