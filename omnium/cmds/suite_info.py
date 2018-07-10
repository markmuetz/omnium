"""Shows useful information about a suite"""
from logging import getLogger
from omnium.bcolors import bcolors

logger = getLogger('om.suite_info')

ARGS = []


def main(suite, args):
    bcolors.print('= Suite: {} ='.format(suite.name), ['HEADER', 'BOLD'])
    print('')
    bcolors.print('== Suite info: ==', ['BOLD'])
    for line in suite.info_lines():
        print(line)
    print('')
    if suite.is_init:
        bcolors.print('== Suite config: ==', ['BOLD'])
        for line in suite.suite_config_lines():
            print(line)
