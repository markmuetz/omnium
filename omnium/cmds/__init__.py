from collections import OrderedDict
import importlib
from logging import getLogger

logger = getLogger('omni')

commands = [
    'convert',
    'run',
    'shell',
    'stash',
    'suite-info',
    'version',
    'viewer',
]

modules = OrderedDict()
for command in commands:
    command_name = 'cmds.' + command.replace('-', '_')
    try:
        modules[command] = importlib.import_module('omnium.' + command_name)
    except ImportError, e:
        logger.info('Cannot load module {}'.format(command_name))
        logger.info(e)
