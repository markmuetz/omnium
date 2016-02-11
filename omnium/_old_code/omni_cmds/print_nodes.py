"""Print all nodes grouped by batch, group"""
ARGS = [(['--computer'], {'nargs': '?'})]


def main(args, config, process_classes):
    from omnium.node_dag import NodeDAG

    if args.computer:
        dag = NodeDAG(config, process_classes, args.computer)
    else:
        dag = NodeDAG(config, process_classes)
    dag.print_nodes()
