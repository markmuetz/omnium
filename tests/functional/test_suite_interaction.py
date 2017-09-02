import os
import shutil
from glob import glob

from omnium.omnium_cmd import main as omnium_main

SCRATCH_DIR = '_function_suite_interaction_scratch'
origcwd = ''


def setup():
    global origcwd
    origcwd = os.getcwd()

    os.environ['OMNIUM_ANALYZERS_PATH'] = os.path.join(origcwd, 'test_analysers')

    if os.path.exists(SCRATCH_DIR):
        shutil.rmtree(SCRATCH_DIR)
    os.makedirs(SCRATCH_DIR)
    os.chdir(SCRATCH_DIR)


def teardown():
    global origcwd
    os.chdir(origcwd)
    shutil.rmtree(SCRATCH_DIR)


def test_sanity():
    dirname = os.getcwd()
    dirname2 = os.path.join(origcwd, SCRATCH_DIR)
    assert dirname == dirname2


def test_clone():
    global origcwd
    suite_dir = os.path.join(origcwd, 'test_suite')
    omnium_main(['omnium', 'suite-clone',
                 '--host-name=localhost', '--host=localhost',
                 '--base-path={}'.format(suite_dir),
                 'u-ap347'])
    os.chdir('u-ap347')


def test_fetch():
    # N.B. globbing *will not work* as it's normally handled by shell.
    filepath_glob = 'share/data/history/S0/atmos.000.pp1.csv'
    filenames = glob(filepath_glob)

    for filename in filenames:
        assert os.path.islink(filename)

    omnium_main(['omnium', 'fetch'] + filenames)
    for filename in filenames:
        assert not os.path.islink(filename)

def test_run():
    omnium_main(['omnium', 'run', '-a', 'csv_analysis', 'S0'])
