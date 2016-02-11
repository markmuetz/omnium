import os
import shutil
from logging import getLogger

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
        from omnium.remote_transfer import RemoteTransfer

        self.force = force
        self.config = config
        self.remote = RemoteInfo(config)
        self.remote_tx = RemoteTransfer()

    def sync_node_dag(self, process_classes):
        '''Sync node dag from remote computer to current'''
        # Copies across sqlite3 db, renames it, renames computer in it, then updates
        # all nodes' statuses.

        # Copy sqlite3 from remote.
        from omnium.node_dag import NodeDAG

        computer_name = self.config['computer_name']
        sqlite3_remote_path = os.path.join(self.remote.path, '.omni', 'sqlite3.db')
        if not os.path.exists('.omni'):
            os.makedirs('.omni')
        local_path = os.path.join('.omni', '{}_sqlite3.db'.format(self.remote.computer_name))

        self.remote_tx.transfer_file(self.remote.address,
                                     sqlite3_remote_path,
                                     local_path)

        # Rename.
        sqlite3_local_path = os.path.join('.omni', 'sqlite3.db')
        shutil.copyfile(local_path, sqlite3_local_path)

        # Update (new) local dag.
        dag = NodeDAG(self.config, process_classes)
        computers = dag.get_computers()
        assert(len(computers) == 1)
        computer = computers[0]
        computer.name = computer_name

        dag.commit()
        dag.verify_status(update=True)

        self.dag = dag
        self.remote_dag = NodeDAG(self.config, process_classes,
                                  self.remote.computer_name)

        return dag

    def sync_batch(self, batch):
        for group in batch.groups:
            self.sync_group(group, False)
        self.dag.verify_status(update=True)
        return batch

    def sync_group(self, group, verify=True):
        for node in group.nodes:
            self.sync_node(node, False)
        if verify:
            self.dag.verify_status(update=True)
        return group

    def sync_node(self, node, verify=True):
        if node.status == 'done':
            logger.info('Local node {} has already been processed'.format(node))
            if self.force:
                logger.info('Forcing resync from remote computer')
            else:
                return None

        logger.debug('Getting remote node {}'.format(node))
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

        try:
            self.remote_tx.get_node(self.remote.address,
                                    remote_filename,
                                    local_filename)
        except Exception:
            self.dag.verify_status(update=True)
            raise

        logger.debug('appending metadata to .done file')
        with open(local_filename + '.done', 'a') as outfile:
            outfile.write('Copied from {}\n'.format(self.remote.computer_name))

        if verify:
            self.dag.verify_status(update=True)
        return node

    def sync_dir(self, dirname):
        computer_name = self.config['computer_name']
        local_dir = self.config['computers'][computer_name]['dirs'][dirname]
        remote_dir = self.config['computers'][self.remote.computer_name]['dirs'][dirname]

        if not os.path.exists(local_dir):
            os.makedirs(local_dir)

        self.remote_tx.get_dir(self.remote.address, remote_dir, local_dir)
        self.dag.verify_status(update=True)
