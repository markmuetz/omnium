"""Verify status of all nodes"""
ARGS = [(['--update'], {'action': 'store_true'})]


def main(args, config, process_classes):
    from omnium.node_dag import NodeDAG

    dag = NodeDAG(config, process_classes)
    dag.verify_status(args.update)
