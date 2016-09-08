# Test omni_conf.py file.
from collections import OrderedDict as odict

settings = {
    'ignore_warnings': True,
}

computer_name = '{{ computer_name | default("zerogravitas")}}'
computers = {
    'zerogravitas': {
        'dirs': {
            '{{ work | default("work") }}': 'work',
            '{{ results | default("results") }}': 'results',
            '{{ output | default("output") }}': 'output'
        }
    }
}

batches = odict(('batch{}'.format(i), {'index': i}) for i in range(4))

groups = odict([
    ('group1', {
        'type': 'init',
        'base_dir': 'work',
        'batch': 'batch0',
        'filename_glob': 'item.???.txt',
    }),
    ('processed_group', {
        'type': 'group_process',
        'from_group': 'group1',
        'base_dir': 'results',
        'batch': 'batch1',
        'process': 'proc1',
    }),
    ('useful_analysis', {
        'type': 'nodes_process',
        'base_dir': 'results',
        'batch': 'batch2',
        'nodes': ['{{ node1 | default("node1") }}', 'node2'],
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
        'process': 'proc2',
        'process_args': 'node1_replace',
    }),
    ('node2', {
        'type': 'from_group',
        'from_group': 'processed_group',
        'variable': 'v2',
        'process': 'proc2',
        'process_args': 'node2_replace',
    }),
    ('node3', {
        'type': 'from_nodes',
        'from_nodes': ['node1', 'node2'],
        'process': 'proc3',
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
