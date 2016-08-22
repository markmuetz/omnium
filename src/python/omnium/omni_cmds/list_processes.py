"""List all processes including locally defined ones"""
from omnium.processes import get_process_classes

ARGS = []

def main(args, config):
    process_classes = get_process_classes(args.cwd)
    for k, v in process_classes.items():
        print(k)
