import os
import sys
import shutil
import importlib

from nose import with_setup

from jinja2 import Environment, FileSystemLoader

sys.path.insert(0, '../src/python')

# Gets around PEP8 checks.
check_config = importlib.import_module('omnium.check_config')
ConfigChecker = check_config.ConfigChecker
sys.path.remove('../src/python')

working_test_dir = 'unit/config/_working_test_dir'

process_classes = {
    'proc1': None,
    'proc2': None,
    'proc3': None
}

contexts = [
    (True, {'node1': 'node1'}),
    (False, {'node1': 'node_doesnt_exist'}),
    (False, {'work': 'not_work'}),
]


def _setup():
    if os.path.exists(working_test_dir):
        shutil.rmtree(working_test_dir)
    os.makedirs(working_test_dir)


def _teardown():
    if os.path.exists(working_test_dir):
        shutil.rmtree(working_test_dir)


@with_setup(_setup, _teardown)
def test_generator():
    tpl_env = Environment(
                autoescape=False,
                loader=FileSystemLoader('unit/config/templates'),
                trim_blocks=False)

    for success, test_context in contexts:
        yield _test_config, tpl_env, success, test_context


def _test_config(tpl_env, success, test_context):
    tpl_render = tpl_env.get_template('omni_conf.py').render(test_context)

    config_path = os.path.join(working_test_dir, 'omni_conf.py')
    with open(config_path, 'w') as f:
        f.write(tpl_render)

    config = ConfigChecker.load_config(config_path)
    config_checker = ConfigChecker(config, process_classes, raise_errors=False)
    # config_checker = ConfigChecker(config, process_classes)
    config_checker.run_checks()

    if success:
        print(config_checker.errors)
        assert not config_checker.errors, "Checker raised errors"
    else:
        assert config_checker.errors, "Checker did not raise errors"
