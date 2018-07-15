"""Displays information about experiments"""
from omnium.bcolors import bcolors
from omnium.suite import ExptList

ARGS = [(['expts'], {'nargs': '*', 'help': 'Experiments to display'}),
        (['--long', '-l'], {'help': 'Display extra info', 'action': 'store_true'}),
        (['--all'], {'help': 'Display all experiments', 'action': 'store_true'})]


def main(cmd_ctx, args):
    expts = ExptList(cmd_ctx.suite)
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
            if expt.has_um_config:
                try:
                    print('  um_version: {}'.format(expt.um_version))
                    print('  model_type: {}'.format(expt.model_type))
                    print('  dt: {} s'.format(expt.dt))
                    print('  nx: {}'.format(expt.nx))
                    print('  ny: {}'.format(expt.ny))
                    if expt.model_type == 'LAM_bicyclic':
                        print('  dx: {} m'.format(expt.dx))
                        print('  dy: {} m'.format(expt.dy))
                        print('  lx: {} m'.format(expt.lx))
                        print('  ly: {} m'.format(expt.ly))
                except (ValueError, KeyError) as e:
                    print('Could not read properties for {}: {}'.format(expt.name, repr(e)))
