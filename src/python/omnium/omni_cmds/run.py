"""Run an omni"""
import os
import convert
import process
import gen_output

ARGS = []

def main(args, config):
    settings = config.settings
    if settings.convert:
        convert.main(args, config)
    if settings.process:
        process.main(args, config)
    if settings.gen_output:
        gen_output.main(args, config)
