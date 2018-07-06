import os
import sys
import shutil
from glob import glob

from omnium.omnium_cmd import main as omnium_main
from omnium.setup_logging import setup_logger

SCRATCH_DIR = '_function_suite_interaction_scratch'

origcwd = ''


def setup():
    global origcwd
    origcwd = os.getcwd()
    print(origcwd)
    #sys.path.insert(0, os.path.join(origcwd, 'test_analysers'))

    os.environ['OMNIUM_ANALYSER_PKGS'] = 'omnium.tests.test_analysers.analysis'

    if os.path.exists(SCRATCH_DIR):
        shutil.rmtree(SCRATCH_DIR)
    os.makedirs(SCRATCH_DIR)
    os.chdir(SCRATCH_DIR)

    setup_logger()


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


def test_suite_info():
    omnium_main(['omnium', 'suite-info'])


def test_suite_init():
    omnium_main(['omnium', 'suite-init', '--suite-type', 'mirror'])


def test_ls_analysers():
    omnium_main(['omnium', 'ls-analysers'])
    omnium_main(['omnium', 'ls-analysers', '--long'])


def test_file_info():
    omnium_main(['omnium', 'file-info', 'share/data/history/S0/atmos.000.pp1.csv'])
    omnium_main(['omnium', 'file-info', '--long', 'share/data/history/S0/atmos.000.pp1.csv'])


def test_clean_symlinks():
    omnium_main(['omnium', 'clean-symlinks', '--dry-run'])
    # You *MUST* sync after doing this.
    omnium_main(['omnium', 'clean-symlinks'])


def test_sync():
    # DO NOT REMOVE.
    omnium_main(['omnium', 'sync'])


def test_file_cat():
    omnium_main(['omnium', 'file-cat', 'share/data/history/S0/atmos.000.pp1.csv'])


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
    # Creates a file atmos.000.pp1.csv.out - send back to remote in send.
    omnium_main(['omnium', 'run', '-t', 'expt', '-a', 'csv_analysis', 'S0'])


def test_run2():
    omnium_main(['omnium', 'run', '-t', 'expt', '-a', 'csv_analysis', 'S0'])


def test_send():
    filename = 'share/data/history/S0/atmos.000.pp1.csv.out'
    suite_dir = os.path.join(origcwd, 'test_suite/u-ap347')
    remote_filename = os.path.join(suite_dir, filename)
    assert not os.path.exists(remote_filename)
    omnium_main(['omnium', 'send', filename])
    assert os.path.exists(remote_filename)
    os.remove(remote_filename)
    
    
def test_remote_command():
    omnium_main(['omnium', 'remote-cmd', 'du -hs'])
