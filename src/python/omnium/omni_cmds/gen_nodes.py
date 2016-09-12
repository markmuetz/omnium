"""Generates all nodes from config"""
ARGS = [(['--disable-print'], {'help': 'Disable printing of graph',
                               'action': 'store_true',
                               'default': False}),
        (['--regen'], {'help': 'Regenerate node graph from scratch',
                       'action': 'store_true',
                       'default': False}),
        (['--force', '-f'], {'help': 'Force running of command if remote computer set',
                             'action': 'store_true',
                             'default': False})]


def main(args, config, process_classes):
    from omnium.node_dag import NodeDAG

    local_computer_name = config['computer_name']
    if ('remote' in config['computers'][local_computer_name] and not args.force):
        msg = 'This computer ({}) has a remote computer defined\n'\
              'If you really want to run this command use --force'\
              .format(local_computer_name)
        raise Exception(msg)

    if args.regen:
        dag = NodeDAG.regenerate(config, process_classes)
    else:
        dag = NodeDAG.generate(config, process_classes)

    if not args.disable_print:
        dag.print_nodes()
