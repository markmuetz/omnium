import subprocess as sp
from logging import getLogger

logger = getLogger('omni')


class RemoteTransfer(object):
    def transfer_file(self, address, remote_path, local_path):
        cmd = 'scp {}:{} {}'.format(address, remote_path, local_path)
        logger.debug(cmd)
        try:
            logger.debug(sp.check_output(cmd.split()))
        except sp.CalledProcessError as e:
            msg = 'error code {}'.format(e.returncode)
            logger.error(msg)
            msg = 'output\n{}'.format(e.output)
            logger.error(msg)
            raise Exception('Failed to copy remote database')
        return local_path

    def get_node(self, address, remote_path, local_path):
        self.transfer_file(address, remote_path, local_path)
        self.transfer_file(address, remote_path + '.done', local_path + '.done')

        return local_path

    def get_dir(self, address, remote_dir, local_dir):
        # N.B trailing slash on source dir is important. Tells rsync to not
        # create new dir e.g. results/results/
        cmd = 'rsync -avz {}:{}/ {}'.format(address, remote_dir, local_dir)
        logger.debug(cmd)
        try:
            logger.debug('\n' + sp.check_output(cmd.split()))
        except sp.CalledProcessError as e:
            msg = 'error code {}'.format(e.returncode)
            logger.error(msg)
            msg = 'output\n{}'.format(e.output)
            logger.error(msg)
            raise Exception('Failed to copy remote database')
        return local_dir
