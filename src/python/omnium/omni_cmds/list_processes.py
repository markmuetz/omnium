"""List all processes including locally defined ones"""
from omnium.processes import process_classes

ARGS = []


def main(args, config):
    maxlen = max([len(k) for k in process_classes.keys()])
    for k, v in process_classes.items():
        fmt = '{0:' + str(maxlen) + '}: {1}'
        print(fmt.format(k, v))
