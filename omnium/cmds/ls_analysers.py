"""Returns information on currently installed analysers"""
import os

from omnium.analysis import AnalysisPkgs

ARGS = [(['-l', '--long'], {'help': 'print long version', 'action': 'store_true'})]


def main(cmd_ctx, args):
    analysis_pkgs = cmd_ctx.analysis_pkgs
    maxlen = max([len(k) for k in analysis_pkgs.analyser_classes.keys()])

    if args.long:
        fmt = '{0:' + str(maxlen) + '}: {1:8}, {2:20}, {3}'
        print(fmt.format('Name', 'S/MF/ME', 'Pkg', 'Class_name'))
        print('')
        for name, cls in analysis_pkgs.analyser_classes.items():
            atype = ''.join([str(1*v) for v in [cls.single_file, cls.multi_file, cls.multi_expt]])
            print(fmt.format(name, atype, analysis_pkgs.get_package(cls).name, cls))
    else:
        fmt = '{0:' + str(maxlen) + '}: {1}'
        print(fmt.format('Name', 'Class_name'))
        print('')
        for name, cls in analysis_pkgs.analyser_classes.items():
            print(fmt.format(name, cls))
