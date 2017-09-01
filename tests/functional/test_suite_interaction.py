import os
import shutil
import subprocess as sp

from omnium.omnium_cmd import main as omnium_main

SCRATCH_DIR = '_function_suite_interaction_scratch'
origcwd = ''


def setup():
    global origcwd
    origcwd = os.getcwd()

    if os.path.exists(SCRATCH_DIR):
        shutil.rmtree(SCRATCH_DIR)
    os.makedirs(SCRATCH_DIR)
    os.chdir(SCRATCH_DIR)
    # TODO: Need to put bin/omnium at start of path...
    # os.putenv('PATH', os.getenv('PATH'))


def teardown():
    global origcwd
    os.chdir(origcwd)
    shutil.rmtree(SCRATCH_DIR)


def test_sanity():
    dirname = os.getcwd()
    dirname2 = os.path.join(origcwd, SCRATCH_DIR)
    assert dirname == dirname2


def test_clone():
    omnium_main(['omnium', 'suite-clone',
                 '--host-name=localhost', '--host=localhost',
                 '--base-path=/home/markmuetz/archer_mirror/nerc/um10.7_runs/postproc',
                 'u-ap347'])
    os.chdir('u-ap347')


def test_fetch():
    omnium_main(['omnium', 'fetch',
                 'share/data/history/S0/figs/*'])
