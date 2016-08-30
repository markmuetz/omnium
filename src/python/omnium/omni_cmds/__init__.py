from collections import OrderedDict
import importlib

commands = [
    'config-get', 
    'config-set', 
    'config-del',
    'file-info',
    'gen-node-graph', 
    'list-files',
    'list-processes',
    'print-config', 
    'print-node-graph', 
    'process-batch', 
    'remote-node-sync', 
    'remote-get-dir', 
    'run', 
    'shell', 
    'threed',
    'verify-node-graph', 
    ]

modules = OrderedDict()
for command in commands:
    command_name = 'omni_cmds.' + command.replace('-', '_')
    try:
        modules[command] = importlib.import_module(command_name)
    except ImportError, e:
        print('Cannot load module {}'.format(command_name))
        print(e)
