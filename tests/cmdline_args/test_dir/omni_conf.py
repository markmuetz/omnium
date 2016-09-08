# Test omni_conf.py file.
from collections import OrderedDict as odict

settings = {
    'ignore_warnings': True,
}

computer_name = open('computer.txt').read().strip()
computers = {
    'zerogravitas': {
        'dirs': {
            'work': 'work',
            'results': 'results',
            'output': 'output'
        }
    }
}

batches = odict(('batch{}'.format(i), {'index': i}) for i in range(4))

groups = odict([
    ('init_group', {
        'type': 'init',
        'base_dir': 'work',
        'batch': 'batch0',
        'filename_glob': 'item.???.txt',
    }),
    ('processed_group', {
        'type': 'group_process',
        'from_group': 'init_group',
        'base_dir': 'results',
        'batch': 'batch1',
        'process': 'copy_file',
    }),
    ('useful_analysis', {
        'type': 'nodes_process',
        'base_dir': 'results',
        'batch': 'batch2',
        'nodes': ['node1', 'node2'],
    }),
    ('plots', {
        'type': 'nodes_process',
        'base_dir': 'output',
        'batch': 'batch3',
        'nodes': ['node3'],
    }),
])

nodes = odict([
    ('node1', {
        'type': 'from_group',
        'from_group': 'processed_group',
        'variable': 'v1',
        'process': 'text_replace',
        'process_args': 'node1_replace',
    }),
    ('node2', {
        'type': 'from_group',
        'from_group': 'processed_group',
        'variable': 'v2',
        'process': 'text_replace',
        'process_args': 'node2_replace',
    }),
    ('node3', {
        'type': 'from_nodes',
        'from_nodes': ['node1', 'node2'],
        'process': 'text_combine',
    }),
])

variables = {
    'v1': {
        'section': 0,
        'item': 3,
    },
    'v2': {
        'section': 0,
        'item': 4,
    },
}
    
process_options = {
}
