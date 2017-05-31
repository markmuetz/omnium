from collections import OrderedDict
import importlib
from logging import getLogger

logger = getLogger('om.cmds')

commands = [
    'cat-log',
    'clean-symlinks',
    'convert',
    'file-info',
    'file-cat',
    'ls-analyzers',
    'run',
    'shell',
    'stash',
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
