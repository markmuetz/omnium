from __future__ import print_function

import os
import re
from logging import getLogger

logger = getLogger('om.cat_log')

ARGS = [(['--search', '-s'], {'help': 'Regex to search for'}),
        (['--level', '-l'], {'help': 'Logging level'})]


def main(suite, args):
    cwd = os.getcwd()
    os.chdir(suite.suite_dir)
    with open(suite.logging_filename, 'r') as f:
        log_lines = f.readlines()
    for line in log_lines:
        if args.search:
            if re.search(args.search, line):
                print(line, end='')
        elif args.level:
            split_line = line.split(':')
            if len(split_line) >= 6 and re.search(args.level, split_line[4]):
                print(line, end='')
        else:
            print(line, end='')
    os.chdir(cwd)
