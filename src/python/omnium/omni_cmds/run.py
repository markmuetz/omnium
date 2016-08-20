"""Run an omni"""
import os
from process_batch import process_batch

ARGS = []

def main(args, config):
    for batch in ['batch1', 'batch2', 'batch3']:
        process_batch(args, config, batch)
