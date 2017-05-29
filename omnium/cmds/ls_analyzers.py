import os
ARGS = []


def main(args):
    from omnium.suite import Suite

    suite = Suite()
    suite.load(os.getcwd())

    maxlen = max([len(k) for k in suite.analysis_classes.keys()])
    for k, v in suite.analysis_classes.items():
        fmt = '{0:' + str(maxlen) + '}: {1}'
        print(fmt.format(k, v))
