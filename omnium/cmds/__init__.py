import importlib
from collections import OrderedDict
from logging import getLogger

logger = getLogger('om.cmds')

commands = [
    'analyser-info',
    'clean-symlinks',
    'convert',
    'expt-info',
    'file-info',
    'file-cat',
    'ls-analysers',
    'run',
    'remote-cmd',
    'shell',
    'stash',
    'suite-clone',
    'suite-freeze',
    'suite-info',
    'suite-init',
    'suite-unfreeze',
    'sync',
    'fetch',
    'send',
    'version',
    'viewer',
    'test',
]

modules = OrderedDict()
for command in commands:
    command_name = 'cmds.' + command.replace('-', '_')
    try:
        modules[command] = importlib.import_module('omnium.' + command_name)
    except ImportError as e:
        logger.warning('Cannot load module {}'.format(command_name))
        logger.warning(e)
