"""Runs a command on the remote suite"""
import os
from logging import getLogger

from omnium.syncher import Syncher

logger = getLogger('om.fetch')

ARGS = [(['cmd'], {'help': 'Command to run', 'nargs': 1}),
        (['--remote', '-r'], {'help': 'Remote'}),
        (['--verbose', '-v'], {'help': 'Set verbose mode', 'action': 'store_true'})]


def main(cmd_ctx, args):
    syncher = Syncher(cmd_ctx.suite, remote_name=args.remote, verbose=args.verbose)

    rel_dir = os.path.relpath(os.getcwd(), cmd_ctx.suite.suite_dir)
    remote_path = os.path.join(syncher.remote_base_path, cmd_ctx.suite.name)
    logger.debug('run cmd {} on : {} ({}:{})', args.cmd[0],
                 syncher.remote_name, syncher.remote_host, remote_path)
    remote_path, output = syncher.run_cmd(rel_dir, args.cmd[0])
    print('Output from: {} ({}:{})'.format(syncher.remote_name,
                                           syncher.remote_host,
                                           os.path.join(syncher.remote_base_path,
                                                        cmd_ctx.suite.name)))
    print(remote_path)
    print('')
    print(output.decode())
