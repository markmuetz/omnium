import importlib
from collections import OrderedDict
from logging import getLogger

logger = getLogger('om.cmds')

commands = [
    'cat-log',
    'clean-symlinks',
    'convert',
    'file-info',
    'file-cat',
    'ls-analysers',
    'run',
    'shell',
    'stash',
    'suite-clone',
    'suite-info',
    'suite-init',
    'sync',
    'fetch',
    'send',
    'version',
    'viewer',
]

modules = OrderedDict()
for command in commands:
    command_name = 'cmds.' + command.replace('-', '_')
    try:
        modules[command] = importlib.import_module('omnium.' + command_name)
    except ImportError, e:
        logger.warn('Cannot load module {}'.format(command_name))
        logger.warn(e)
