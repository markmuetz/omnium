"""List all processes including locally defined ones"""
from omnium.processes import process_classes

ARGS = []


def main(args, config):
    for k, v in process_classes.items():
        print(k)
