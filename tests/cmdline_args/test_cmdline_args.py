#import sys
#sys.path.insert(0, '../src/python')
import os
import subprocess as sp

#from omnium.command_parser import parse_commands
#from omnium import omni_cmd
#from omnium import omni_cmds

cmds = ['check-config']


def test_generator():
    for cmd in cmds:
        yield _test_command, cmd


def _test_command(cmd):
    os.chdir('cmdline_args/test_dir')
    output = sp.call('omnium ls')
    assert output == 0, "Command raised errors"
