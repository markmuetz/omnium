"""Displays information about experiments"""
from omnium.expt import ExptList
from omnium.bcolors import bcolors

ARGS = [(['expts'], {'nargs': '*', 'help': 'Experiments to display'}),
        (['--long', '-l'], {'help': 'Display extra info', 'action': 'store_true'}),
        (['--all'], {'help': 'Display all experiments', 'action': 'store_true'})]


def main(suite, args):
    expts = ExptList(suite)
    if not expts.config_has_required_info:
        bcolors.print('Required information not in config', ['WARNING', 'BOLD'])
        print('add expt_datam_dir and expt_dataw_dir')
        return

    if args.all:
        expts.find_all()
    else:
        expts.find(args.expts)

    for expt in expts:
        bcolors.print(expt, ['HEADER', 'BOLD'])
        if args.long:
            print('  ' + expt.datam_dir)
            for dataw_dir in expt.dataw_dirs:
                print('  ' + dataw_dir)
            print('  ' + expt.rose_app_run_conf_file)
