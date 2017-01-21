from collections import OrderedDict
import importlib
from logging import getLogger

logger = getLogger('omni')

commands = [
    'convert',
    'create',
    'ls',
    'version',
    'viewer',
    'twod_viewer',
]

modules = OrderedDict()
for command in commands:
    command_name = 'omnium_cmds.' + command.replace('-', '_')
    try:
        modules[command] = importlib.import_module('omnium.' + command_name)
    except ImportError, e:
        logger.info('Cannot load module {}'.format(command_name))
        logger.info(e)
