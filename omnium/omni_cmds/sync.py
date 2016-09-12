"""syncs nodes from remote machine defined in omni_conf.py"""
from logging import getLogger

from omnium.syncher import Syncher

logger = getLogger('omni')

ARGS = [(['--all', '-a'], {'help': 'Perform full sync of nodes/files',
                           'action': 'store_true'}),
        (['--batch', '-b'], {'help': 'Sync of nodes in batch', 'nargs': '?'}),
        (['--group', '-g'], {'help': 'Sync of nodes in group', 'nargs': '?'}),
        (['--node', '-n'], {'help': 'Sync of node', 'nargs': '?'}),
        (['--node-id'], {'help': 'Sync of node by id', 'nargs': '?', 'type': int}),
        (['--dir', '-d'], {'help': 'Sync of directory in config', 'nargs': '?'}),
        (['--meta', '-m'], {'help': 'Sync of node dag only', 'action': 'store_true'}),
        (['--force', '-f'], {'help': 'Force re-transfer of files', 'action': 'store_true'})]


def main(args, config, process_classes):
    syncher = Syncher(args.force, config)
    if args.meta:
        syncher.sync_node_dag(process_classes)
        logger.info('Synced node dag')
    else:
        opts = [args.batch is not None, args.group is not None,
                args.node is not None, args.dir is not None,
                args.node_id is not None]
        if sum(opts) >= 2 or sum(opts) == 0:
            raise Exception('Please select exactly one of --batch, --group or --node')
        dag = syncher.sync_node_dag(process_classes)

        if args.dir:
            syncher.sync_dir(args.dir)
            logger.info('Synced dir {}'.format(args.dir))
        elif args.batch:
            batch = dag.get_batch(args.batch)
            batch = syncher.sync_batch(batch)
            if batch:
                logger.info('Synced batch {}'.format(batch))
        elif args.group:
            group = dag.get_group(args.group)
            group = syncher.sync_group(group)
            if group:
                logger.info('Synced group {}'.format(group))
        elif args.node or args.node_id:
            if args.node_id:
                node = dag.get_node_from_id(args.node_id)
            node = dag.get_node(args.node)
            node = syncher.sync_node(node)
            if node:
                logger.info('Synced node {}'.format(node))
