"""syncs nodes from remote machine defined in omni.conf"""
import os
import shutil
import subprocess as sp
from logging import getLogger

from omnium.node_dag import get_node_dag

logger = getLogger('omni')

ARGS = [(['--all', '-a'], {'help': 'Perform full sync of nodes/files',
                           'action': 'store_true'}),
        (['--batch', '-b'], {'help': 'Sync of nodes in batch', 'nargs': '?'}),
        (['--group', '-g'], {'help': 'Sync of nodes in group', 'nargs': '?'}),
        (['--node', '-n'], {'help': 'Sync of node', 'nargs': '?'}),
        (['--dir', '-d'], {'help': 'Sync of directory in config', 'nargs': '?'}),
        (['--meta', '-m'], {'help': 'Sync of node dag only', 'action': 'store_true'}),
        (['--force', '-f'], {'help': 'Force re-transfer of files', 'action': 'store_true'}),
        ]

class RemoteInfo(object):
    def __init__(self, args, config):
        self.args = args
        self.config = config

        local_computer_name = config['computer_name']
        self.computer_name = config['computers'][local_computer_name]['remote']
        self.address = config['computers'][local_computer_name]['remote_address']
        self.path = config['computers'][local_computer_name]['remote_path']

def sync_node_dag(args, config, remote):
    '''Sync node dag from remote computer to current'''
    # Copies across sqlite3 db, renames it, renames computer in it, then updates
    # all nodes' statuses.

    # Copy sqlite3 from remote.

    computer_name = config['computer_name']
    sqlite3_remote_path = os.path.join(remote.path, '.omni', 'sqlite3.db')
    local_path = os.path.join('.omni', '{}_sqlite3.db'.format(remote.computer_name))

    cmd = 'scp {}:{} {}'.format(remote.address, sqlite3_remote_path, local_path)
    logger.debug(cmd)
    try:
        logger.debug(sp.check_output(cmd.split()))
    except sp.CalledProcessError as e:                                                                                                   
        msg = 'error code {}'.format(e.returncode)
        logger.error(msg)
        msg = 'output\n{}'.format(e.output)
        logger.error(msg)

    # Rename.
    sqlite3_local_path = os.path.join('.omni', 'sqlite3.db')
    shutil.copyfile(local_path, sqlite3_local_path)

    # Update (new) local dag.
    dag = get_node_dag(args, config)
    computers = dag.get_computers()
    assert(len(computers) == 1)
    computer = computers[0]
    computer.name = computer_name
    dag.verify_status(update=True)
    dag.commit()
    return dag


def sync_batch(args, config, remote, dag, batch):
    for group in batch.groups:
        sync_group(args, config, remote, dag, group)
    batch.status == 'done'
    dag.commit()
    return batch


def sync_group(args, config, remote, dag, group):
    for node in group.nodes:
        sync_node(args, config, remote, dag, node)
    group.status == 'done'
    dag.commit()
    return group


def sync_node(args, config, remote, dag, node):
    if node.status == 'done':
        logger.info('Local node {} has already been processed'.format(node))
        if args.force:
            logger.info('Forcing resync from remote computer')
        else:
            return None

    remote_dag = get_node_dag(args, config, remote.computer_name)
    remote_node = remote_dag.get_node(node.name)
    if remote_node.status != 'done':
        logger.error('Remote node has not been processed yet')
        return None

    logger.info('Syncing node {}'.format(node))
    remote_filename = node.filename(config, remote.computer_name)
    local_filename = node.filename(config)
    dirname = os.path.dirname(local_filename)
    if not os.path.exists(dirname):
        logger.debug('Creating dir {}'.format(dirname))
        os.makedirs(dirname)
    cmd = 'scp {}:{} {}'.format(remote.address, remote_filename, local_filename)
    logger.debug(cmd)
    try:
        logger.debug(sp.check_output(cmd.split()))
    except sp.CalledProcessError as e:                                                                                                   
        msg = 'error code {}'.format(e.returncode)
        logger.error(msg)
        msg = 'output\n{}'.format(e.output)
        logger.error(msg)

    with open(local_filename + '.done', 'w') as f:
        f.write('Copied from {}'.format(remote.computer_name))

    node.status = 'done'
    dag.commit()
    return node


def sync_dir(args, config, remote, dag, dirname):
    computer_name = config['computer_name']
    local_dir = config['computers'][computer_name]['dirs'][dirname]
    remote_dir = config['computers'][remote.computer_name]['dirs'][dirname]

    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    # N.B trailing slash on source dir is important. Tells rsync to not 
    # create new dir e.g. results/results/
    cmd = 'rsync -avz {}:{}/ {}'.format(remote.address, remote_dir, local_dir)
    logger.debug(cmd)
    logger.debug('\n' + sp.check_output(cmd.split()))

    dag.verify_status(update=True)


def main(args, config):
    remote = RemoteInfo(args, config)
    if args.meta:
        sync_node_dag(args, config, remote)
        logger.info('Synced node dag')
    else:
        opts = [args.batch != None, args.group != None, args.node != None, args.dir != None]
        if sum(opts) >= 2 or sum(opts) == 0:
            raise Exception('Please select exactly one of --batch, --group or --node')
        dag = sync_node_dag(args, config, remote)

        if args.dir:
            sync_dir(args, config, remote, dag, args.dir)
            logger.info('Synced dir {}'.format(args.dir))
        elif args.batch:
            batch = dag.get_batch(args.batch)
            batch = sync_batch(args, config, remote, dag, batch)
            if batch:
                logger.info('Synced batch {}'.format(batch))
        elif args.group:
            group = dag.get_group(args.group)
            group = sync_group(args, config, remote, dag, group)
            if group:
                logger.info('Synced group {}'.format(group))
        elif args.node:
            node = dag.get_node(args.node)
            node = sync_node(args, config, remote, dag, node)
            if node:
                logger.info('Synced node {}'.format(node))

