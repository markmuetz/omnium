"""Displays information about analyser(s)"""
import os
import inspect

from omnium.omnium_errors import OmniumError
from omnium.analyser import Analyser
from omnium.analysers import Analysers
from omnium.bcolors import bcolors

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


def main(suite, args):
    omnium_analyser_pkgs = os.getenv('OMNIUM_ANALYSER_PKGS')
    analyser_pkg_names = []
    if omnium_analyser_pkgs:
        analyser_pkg_names = omnium_analyser_pkgs.split(':')
    analysers = Analysers(analyser_pkg_names)
    analysers.find_all()

    all_analysers = []
    if args.all:
        all_analysers = analysers.analysis_classes.values()
    else:
        for analyser_name in args.analysers:
            if analyser_name in analysers.analysis_classes:
                all_analysers.append(analysers.analysis_classes[analyser_name])
            else:
                raise OmniumError('analyser {} not found'.format(analyser_name))
    for analyser_cls in all_analysers:
        _display_info(analyser_cls, args.long)
    if not all_analysers:
        raise OmniumError('No analysers found')
