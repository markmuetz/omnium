"""syncs nodes from remote machine defined in omni.conf"""
import os
import subprocess as sp
from logging import getLogger

logger = getLogger('omni')

ARGS = []

def main(args, config):
    computer_name = open(config['computers']['current'], 'r').read().strip()
    remote_computer_name = config['computers'][computer_name]['remote']
    remote_address = config['computers'][computer_name]['remote_address']
    remote_path = config['computers'][computer_name]['remote_path']

    sqlit3_remote_path = os.path.join(remote_path, '.omni', 'sqlite3.db')
    local_path = os.path.join('.omni', '{}_sqlite3.db'.format(remote_computer_name))

    cmd = 'scp {}:{} {}'.format(remote_address, sqlit3_remote_path, local_path)
    logger.info(cmd)
    sp.call(cmd.split())
