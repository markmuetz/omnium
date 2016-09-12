import sys
import importlib
import subprocess as sp

modules = [
    'sqlalchemy',
    'numpy',
    'pandas',
    'pylab',
    'iris',
    'IPython',
    'IPython',
    'pyqtgraph',
    'pyqtgraph.Qt',
    'pyqtgraph.opengl',
]

utils = [
    'scp',
    'rsync',
]


def test_module_generator():
    for module in modules:
        yield _test_module_load, module


def _test_module_load(module_name):
    print(module_name)
    try:
        # Iris shows some weird stuff about loading libc/libgeos.
        # Temporarily disconnect stdout.
        if module_name == 'iris':
            old_stderr = sys.stderr
            sys.stderr = sys.stdout
        module = importlib.import_module(module_name)
        if module_name == 'iris':
            sys.stderr = old_stderr
    except ImportError:
        assert False, "Could not load {}".format(module_name)


def test_util_generator():
    for util in utils:
        yield _test_util_load, util


def _test_util_load(util_name):
    try:
        cmd = '{}'.format(util_name)
        print(cmd)
        output = sp.check_output(cmd.split(), stderr=sp.STDOUT)
    except sp.CalledProcessError as e:
        pass
    except OSError:
        assert False, "Could not load {}".format(util_name)
