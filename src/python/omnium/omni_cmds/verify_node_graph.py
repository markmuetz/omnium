"""Print all nodes grouped by batch, group"""
ARGS = [(['--update'], {'action': 'store_true'})]


def main(args, config):
    from omnium.node_dag import NodeDAG

    dag = NodeDAG(config, process_classes)
    dag.verify_status(args.update)
