"""Returns information on currently installed analysers"""
import os

from omnium.analysers import Analysers

ARGS = [(['-l', '--long'], {'help': 'print long version',
                            'action': 'store_true'})]
RUN_OUTSIDE_SUITE = True


def main(suite, args):
    omnium_analyser_pkgs = os.getenv('OMNIUM_ANALYSER_PKGS')
    analyser_pkg_names = []
    if omnium_analyser_pkgs:
        analyser_pkg_names = omnium_analyser_pkgs.split(':')
    analysers = Analysers(analyser_pkg_names)
    analysers.find_all()
    maxlen = max([len(k) for k in analysers.analysis_classes.keys()])

    if args.long:
        fmt = '{0:' + str(maxlen) + '}: {1:8}, {2:20}, {3}'
        print(fmt.format('Name', 'S/MF/ME', 'Group', 'Class_name'))
        print('')
        for name, cls in analysers.analysis_classes.items():
            atype = ''.join([str(1*v) for v in [cls.single_file, cls.multi_file, cls.multi_expt]])
            print(fmt.format(name, atype, analysers.analysis_groups[name], cls))
    else:
        fmt = '{0:' + str(maxlen) + '}: {1}'
        print(fmt.format('Name', 'Class_name'))
        print('')
        for name, cls in analysers.analysis_classes.items():
            print(fmt.format(name, cls))
