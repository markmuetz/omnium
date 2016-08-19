"""Generate output"""
import os

import omnium.outputters

ARGS = []

def main(args, config):
    for output_fn_name in config.output_fn_names.options():
        sec = getattr(config, output_fn_name)
        outputter = getattr(omnium.outputters, output_fn_name)
        print(outputter)
