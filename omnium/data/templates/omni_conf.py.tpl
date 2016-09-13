# Demonstration omni_conf.py file.
# Please replace all values.
from collections import OrderedDict as odict

settings = {
    'ignore_warnings': True,
}

computer_name = open('computer.txt').read().strip()
computers = {
    '{{ computer_name }}': {
        'dirs': {
            'work': '/path/to/work',
            'results': '/path/to/results',
            'output': '/path/to/output'
        }
    }
}

batches = odict(('batch{}'.format(i), {'index': i}) for i in range(4))

groups = odict([
    ('init_group', {
        'type': 'init',
        'base_dir': 'work',
        'batch': 'batch0',
        'filename_glob': 'atmos.???.pp5',
    }),
    ('processed_group', {
        'type': 'group_process',
        'from_group': 'init_group',
        'base_dir': 'results',
        'batch': 'batch1',
        'process': 'convert_pp_to_nc',
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
        'variable': 'q',
        'process': 'domain_mean',
    }),
    ('node2', {
        'type': 'from_group',
        'from_group': 'processed_group',
        'variable': 'theta',
        'process': 'domain_mean',
    }),
    ('node3', {
        'type': 'from_nodes',
        'from_nodes': ['node1', 'node2'],
        'process': 'domain_mean',
    }),
])

variables = {
    'q': {
        'section': 0,
        'item': 10,
    },
    'theta': {
        'section': 0,
        'item': 4,
    },
}
    
process_options = {
    'convert_pp_to_nc': {
        'convert_from': '.pp',
        'convert_to': '.nc',
    }
}
