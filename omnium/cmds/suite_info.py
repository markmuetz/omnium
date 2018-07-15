"""Shows useful information about a suite"""
from logging import getLogger

from omnium.bcolors import bcolors

logger = getLogger('om.suite_info')

ARGS = []


def main(cmd_ctx, args):
    bcolors.print('= Suite: {} ='.format(cmd_ctx.suite.name), ['HEADER', 'BOLD'])
    print('')
    bcolors.print('== Suite info: ==', ['BOLD'])
    for line in cmd_ctx.suite.info_lines():
        print(line)
    print('')
    if cmd_ctx.suite.is_init:
        bcolors.print('== Suite config: ==', ['BOLD'])
        for line in cmd_ctx.suite.suite_config_lines():
            print(line)
