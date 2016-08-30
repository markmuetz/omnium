"""syncs nodes from remote machine defined in omni.conf"""
import os
import subprocess as sp

ARGS = [(['dirname'], {'nargs': 1})]

def main(args, config):
    computer_name = open(config['computers']['current'], 'r').read().strip()
    remote_computer_name = config['computers'][computer_name]['remote']
    remote_address = config['computers'][computer_name]['remote_address']

    local_dir = config['computers'][computer_name]['dirs'][args.dirname[0]]
    remote_dir = config['computers'][remote_computer_name]['dirs'][args.dirname[0]]

    if not os.path.exists(local_dir):
        os.makedirs(local_dir)
    # N.B trailing slash on source dir is important. Tells rsync to not 
    # create new dir e.g. results/results/
    cmd = 'rsync -avz {}:{}/ {}'.format(remote_address, remote_dir, local_dir)
    print(cmd)
    sp.call(cmd.split())