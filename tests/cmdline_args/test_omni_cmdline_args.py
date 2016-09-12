import os
import subprocess as sp
import shutil

from nose import with_setup

cmd_args = [
    ('check-config', [None, '--warnings-as-errors']),
    ('list-processes', [None]),
    ('version', [None, '-l']),
    ('view-log', [None, '--level WARNING', '--only-level ERROR',
                  '--from-time 2016-09-09-19:40:00',
                  '--search cmd']),
    ('print-config', [None, 'groups', 'groups useful_analysis',
                      'groups useful_analysis type']),
    ('gen-nodes', [None, '--regen', '--regen --disable-print',
                   '--regen --force']),
    ('print-nodes', [None]),
    ('process', ['-b batch1', '-b batch2', '-b batch3', '-fb batch3',
                 '-fg useful_analysis', '-fn item.002.copy.txt',
                 '--force --all']),
    ('node-info', ['item.001.txt', 'item.002.copy.txt']),
    ('verify-node-statuses', [None, '--update']),
    ('create-process', ['proc1', 'proc2 --baseclass IrisProcess']),
]


def _setup():
    cwd = os.getcwd()
    test_dir = os.path.join(cwd, 'cmdline_args/test_dir')
    working_test_dir = os.path.join(cwd,
                                    'cmdline_args/_working_test_dir')
    if os.path.exists(working_test_dir):
        shutil.rmtree(working_test_dir)
    shutil.copytree(test_dir, working_test_dir)

    os.chdir('cmdline_args/_working_test_dir')


def _teardown():
    os.chdir('../../')
    if os.path.exists('cmdline_args/_working_test_dir'):
        shutil.rmtree('cmdline_args/_working_test_dir')


@with_setup(_setup, _teardown)
def test_generator():
    for cmd, args in cmd_args:
        for arg in args:
            yield _test_command, cmd, arg


def _test_command(cmd, arg):
    if arg:
        cmd_string = 'omni {} {}'.format(cmd, arg)
    else:
        cmd_string = 'omni {}'.format(cmd)
    print(cmd_string)
    try:
        output = sp.check_output(cmd_string.split(), stderr=sp.STDOUT)
    except sp.CalledProcessError as e:
        print('Return code: {}'.format(e.returncode))
        print(e.output)
        assert False, "Command raised errors"
