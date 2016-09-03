from collections import OrderedDict
import importlib
from logging import getLogger

commands = ['ls', 'create']

logger = getLogger('omni')

modules = OrderedDict()
for command in commands:
    command_name = 'omnium_cmds.' + command.replace('-', '_')
    try:
        modules[command] = importlib.import_module(command_name)
    except ImportError, e:
        logger.error('Cannot load module {}'.format(command_name))
        logger.error(e)
