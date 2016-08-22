from collections import OrderedDict
import importlib

commands = [
    'config-get', 
    'config-set', 
    'config-del',
    'file-info',
    'list-files',
    'list-processes',
    'print-config', 
    'print-node-graph', 
    'process-batch', 
    'run', 
    'threed',
    ]

modules = OrderedDict()
for command in commands:
    command_name = 'omni_cmds.' + command.replace('-', '_')
    try:
        modules[command] = importlib.import_module(command_name)
    except ImportError, e:
        print('Cannot load module {}'.format(command_name))
        print(e)
