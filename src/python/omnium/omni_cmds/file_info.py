"""Print info about a given file"""
import os
from glob import glob

import iris

ARGS = [(['--full-path'], {'help': 'show full path of files',
                           'action': 'store_true',
                           'default': False}),
        (['filename'], {'help': 'File to get info for ', }),
        ]

def main(args, config):
    raise NotImplementedError('Implement by 0.5')
