import os
import subprocess as sp
import shutil

cmd_args = [
    ('check-config', [None, '--warnings-as-errors']),
    ('list-processes', [None]),
    ('version', [None, '-l']),
    ('view-log', [None, '--level WARNING', '--only-level ERROR',
                  '--from-time 2016-09-09-19:40:00',
                  '--search cmd']),
    ('print-config', [None, 'groups', 'groups useful_analysis',
                      'groups useful_analysis type']),
    ('gen-node-graph', [None, '--regen', '--regen --disable-print', 
                        '--regen --force']),
    ('print-node-graph', [None]),
    ('process', ['-b batch1', '-b batch2', '-b batch3', '-fb batch3',
                 '-fg useful_analysis', '-fn item.002.copy.txt', 
                 '--force --all']),
    ('node-info', ['item.001.txt', 'item.002.copy.txt']),
    ('verify-node-graph', [None, '--update']),
]


def test_generator():
    cwd = os.getcwd()
    if os.path.exists('cmdline_args/working_test_dir'):
        shutil.rmtree('cmdline_args/working_test_dir')
    shutil.copytree('cmdline_args/test_dir',
                    'cmdline_args/working_test_dir')

    os.chdir('cmdline_args/working_test_dir')

    for cmd, args in cmd_args:
        for arg in args:
            yield _test_command, cmd, arg

    os.chdir(cwd)
    if os.path.exists('cmdline_args/working_test_dir'):
        shutil.rmtree('cmdline_args/working_test_dir')


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
