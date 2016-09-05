from collections import OrderedDict
import importlib
from logging import getLogger

logger = getLogger('omni')

commands = [
    'check-config', 
    'node-info',
    'gen-node-graph', 
    'list-files',
    'list-processes',
    'print-config', 
    'print-node-graph', 
    'process', 
    'sync', 
    'shell', 
    #'threed',
    'verify-node-graph', 
    'version', 
    'view-log', 
    ]

modules = OrderedDict()
for command in commands:
    command_name = 'omni_cmds.' + command.replace('-', '_')
    try:
        modules[command] = importlib.import_module(command_name)
    except ImportError, e:
        logger.info('Cannot load module {}'.format(command_name))
        logger.info(e)
