import os
import shutil
import subprocess as sp
from logging import getLogger

from omnium.node_dag import NodeDAG

logger = getLogger('omni')


class RemoteInfo(object):
    def __init__(self, config):
        self.config = config

        local_computer_name = config['computer_name']
        self.computer_name = config['computers'][local_computer_name]['remote']
        self.address = config['computers'][local_computer_name]['remote_address']
        self.path = config['computers'][local_computer_name]['remote_path']


class Syncher(object):
    def __init__(self, force, config):
        self.force = force
        self.config = config
        self.remote = RemoteInfo(config)

    def sync_node_dag(self):
        '''Sync node dag from remote computer to current'''
        # Copies across sqlite3 db, renames it, renames computer in it, then updates
        # all nodes' statuses.

        # Copy sqlite3 from remote.

        computer_name = self.config['computer_name']
        sqlite3_remote_path = os.path.join(self.remote.path, '.omni', 'sqlite3.db')
        local_path = os.path.join('.omni', '{}_sqlite3.db'.format(self.remote.computer_name))

        cmd = 'scp {}:{} {}'.format(self.remote.address, sqlite3_remote_path, local_path)
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
        dag = NodeDAG(self.config)
        computers = dag.get_computers()
        assert(len(computers) == 1)
        computer = computers[0]
        computer.name = computer_name
        dag.verify_status(update=True)
        dag.commit()

        self.dag = dag
        self.remote_dag = NodeDAG(self.config, self.remote.computer_name)

        return dag

    def sync_batch(self, batch):
        for group in batch.groups:
            self.sync_group(group)
        batch.status == 'done'
        self.dag.commit()
        return batch

    def sync_group(self, group):
        for node in group.nodes:
            self.sync_node(node)
        group.status == 'done'
        self.dag.commit()
        return group

    def sync_node(self, node):
        if node.status == 'done':
            logger.info('Local node {} has already been processed'.format(node))
            if self.force:
                logger.info('Forcing resync from remote computer')
            else:
                return None

        remote_node = self.remote_dag.get_node(node.name, node.group.name)
        if remote_node.status != 'done':
            logger.error('Remote node has not been processed yet')
            return None

        logger.info('Syncing node {}'.format(node))
        remote_filename = node.filename(self.config, self.remote.computer_name)
        local_filename = node.filename(self.config)
        dirname = os.path.dirname(local_filename)
        if not os.path.exists(dirname):
            logger.debug('Creating dir {}'.format(dirname))
            os.makedirs(dirname)
        cmd = 'scp {}:{} {}'.format(self.remote.address, remote_filename, local_filename)
        logger.debug(cmd)
        try:
            logger.debug(sp.check_output(cmd.split()))
        except sp.CalledProcessError as e:
            msg = 'error code {}'.format(e.returncode)
            logger.error(msg)
            msg = 'output\n{}'.format(e.output)
            logger.error(msg)

        with open(local_filename + '.done', 'w') as f:
            f.write('Copied from {}'.format(self.remote.computer_name))

        node.status = 'done'
        self.dag.commit()
        return node

    def sync_dir(self, dirname):
        computer_name = self.config['computer_name']
        local_dir = self.config['computers'][computer_name]['dirs'][dirname]
        remote_dir = self.config['computers'][self.remote.computer_name]['dirs'][dirname]

        if not os.path.exists(local_dir):
            os.makedirs(local_dir)

        # N.B trailing slash on source dir is important. Tells rsync to not
        # create new dir e.g. results/results/
        cmd = 'rsync -avz {}:{}/ {}'.format(self.remote.address, remote_dir, local_dir)
        logger.debug(cmd)
        logger.debug('\n' + sp.check_output(cmd.split()))

        self.dag.verify_status(update=True)
