import os

from omnium.suite import Suite

ARGS = []

def main(args):
    suite = Suite()
    suite.check_in_suite_dir(os.getcwd())

    print('Suite: {}'.format(suite.name))
    print('')
    print('Suite info:')
    print(suite.info())
