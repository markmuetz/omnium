from collections import OrderedDict
import importlib
from logging import getLogger

logger = getLogger('omni')

commands = [
    'check-config',
    'create-process',
    'gen-nodes',
    'list-processes',
    'node-info',
    'print-config',
    'print-nodes',
    'process',
    'sync',
    'shell',
    'threed',
    'verify-node-statuses',
    'version',
    'view-log',
]

modules = OrderedDict()
for command in commands:
    command_name = 'omni_cmds.' + command.replace('-', '_')
    try:
        modules[command] = importlib.import_module('omnium.' + command_name)
    except ImportError, e:
        logger.warn('Cannot load module {}'.format(command_name))
        logger.warn(e)
