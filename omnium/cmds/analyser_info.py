"""Displays information about analyser(s)"""
import inspect

from omnium.analysis import Analyser
from omnium.bcolors import bcolors
from omnium.omnium_errors import OmniumError

ARGS = [(['analysers'], {'nargs': '*', 'help': 'Analyser(s) to get info on'}),
        (['--long', '-l'], {'help': 'Display extra info', 'action': 'store_true'}),
        (['--all'], {'help': 'Display all experiments', 'action': 'store_true'})]
RUN_OUTSIDE_SUITE = True


def _display_info(analyser_cls: Analyser, long: bool) -> Analyser:
    bcolors.print(analyser_cls, ['HEADER', 'BOLD'])
    print('  name: {}'.format(analyser_cls.analysis_name))
    runtype = ('single_file' if analyser_cls.single_file else
               'multi_file' if analyser_cls.multi_file else
               'multi_expt' if analyser_cls.multi_expt else 'Unkown runtype')
    print('  runtype: {}'.format(runtype))
    print('')
    print('  input_dir: {}'.format(analyser_cls.input_dir))
    if analyser_cls.input_filename:
        print('  input_filename: {}'.format(analyser_cls.input_filename))
    elif analyser_cls.input_filenames:
        print('  input_filenames: {}'.format(analyser_cls.input_filenames))
    elif analyser_cls.input_filename_glob:
        print('  input_filename_glob: {}'.format(analyser_cls.input_filename_glob))

    print('  output_dir: {}'.format(analyser_cls.output_dir))
    print('  output_filenames: {}'.format(analyser_cls.output_filenames))
    print('')
    print('  force: {}'.format(analyser_cls.force))
    print('  delete: {}'.format(analyser_cls.delete))
    print('')
    print('  uses_runid: {}'.format(analyser_cls.uses_runid))
    if analyser_cls.uses_runid:
        print('  runid_pattern: {}'.format(analyser_cls.runid_pattern))
        print('  min_runid: {}'.format(analyser_cls.min_runid))
        print('  max_runid: {}'.format(analyser_cls.max_runid))

    if long:
        print('')
        print('  path: {}'.format(inspect.getabsfile(analyser_cls)))
    return analyser_cls


def main(cmd_ctx, args):
    analysis_pkgs = cmd_ctx.analysis_pkgs

    all_analysers = []
    if args.all:
        all_analysers = analysis_pkgs.analyser_classes.values()
    else:
        for analyser_name in args.analysers:
            if analyser_name in analysis_pkgs.analyser_classes:
                all_analysers.append(analysis_pkgs.analyser_classes[analyser_name])
            else:
                raise OmniumError('analyser {} not found'.format(analyser_name))
    for analyser_cls in all_analysers:
        _display_info(analyser_cls, args.long)
    if not all_analysers:
        raise OmniumError('No analysers found')
    return all_analysers
