import os
import subprocess as sp

cmd_args = [
    ('check-config', ['--warnings-as-errors']),
    ('list-processes', []),
    ('version', ['-l']),
    ('view-log', []),
    ('print-config', []),
]


def test_generator():
    cwd = os.getcwd()
    os.chdir('cmdline_args/test_dir')
    for cmd, args in cmd_args:
        yield _test_command, cmd, None
        for arg in args:
            yield _test_command, cmd, arg
    os.chdir(cwd)


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
