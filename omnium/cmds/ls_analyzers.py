import os
ARGS = []


def main(args):
    from omnium.analyzers import get_analysis_classes
    from omnium.suite import Suite

    suite = Suite()
    suite.check_in_suite_dir(os.getcwd())
    analysis_classes = get_analysis_classes(suite.omnium_analysis_dir)
    maxlen = max([len(k) for k in analysis_classes.keys()])
    for k, v in analysis_classes.items():
        fmt = '{0:' + str(maxlen) + '}: {1}'
        print(fmt.format(k, v))
