from collections import OrderedDict
import importlib

commands = ['ls', 'create']

modules = OrderedDict()
for command in commands:
    command_name = 'omnium_cmds.' + command.replace('-', '_')
    try:
        modules[command] = importlib.import_module(command_name)
    except ImportError, e:
        print('Cannot load module {}'.format(command_name))
        print(e)
