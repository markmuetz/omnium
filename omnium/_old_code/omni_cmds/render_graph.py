"""Renders node dag into a png"""
ARGS = [(['--computer'], {'nargs': '?'}),
        (['--outfile'], {'default': 'node_dag.png'}),
        (['--display'], {'action': 'store_true', 'default': False})]


def main(args, config, process_classes):
    from omnium.node_dag import NodeDAG

    if args.computer:
        dag = NodeDAG(config, process_classes, args.computer)
    else:
        dag = NodeDAG(config, process_classes)
    dag.render(args.outfile, args.display)
