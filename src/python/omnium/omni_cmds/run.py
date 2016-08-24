"""Run an omni"""
import os
from process_batch import process_batch
from node_dag import get_node_dag

ARGS = []

def main(args, config):
    for batch in ['batch1', 'batch2', 'batch3']:
        process_batch(args, config, batch)
