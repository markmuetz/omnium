import os

from omnium.analysers import Analysers

ARGS = [(['-l', '--long'], {'help': 'print long version',
                            'action': 'store_true'})]
RUN_OUTSIDE_SUITE = True


def main(suite, args):
    omnium_analysers_paths = os.getenv('OMNIUM_ANALYZERS_PATH')
    if omnium_analysers_paths:
        analyser_dirs = omnium_analysers_paths.split(':')
    analysers = Analysers(analyser_dirs)
    analysers.find_all()
    maxlen = max([len(k) for k in analysers.analysis_classes.keys()])

    if args.long:
        fmt = '{0:' + str(maxlen) + '}: {1:10}, {2:10}, {3}'
        print(fmt.format('Name', 'Multi_file', 'Multi_expt', 'Class_name'))
        print('')
        for name, cls in analysers.analysis_classes.items():
            print(fmt.format(name, str(cls.multi_file), str(cls.multi_expt), cls))
    else:
        fmt = '{0:' + str(maxlen) + '}: {1}'
        print(fmt.format('Name', 'Class_name'))
        print('')
        for name, cls in analysers.analysis_classes.items():
            print(fmt.format(name, cls))
