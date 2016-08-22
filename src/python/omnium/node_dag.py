import os
from collections import OrderedDict
from glob import glob

from results import ResultsManager
from omnium.processes import get_process_classes

class NodeDAG(object):
    def __init__(self, args, config, rm):
        self._args = args
        self._config = config
        self._rm = rm

        self.nodes = []
        self.groups = OrderedDict()
        self.batches = OrderedDict()


    def generate_all_nodes(self, group_names):
        process_classes = get_process_classes(self._args.cwd)

        for i, group_name in enumerate(group_names):
            group_sec = getattr(self._config, group_name)
            group = self._create_group(group_name, 'batch{}'.format(i))
            if hasattr(group_sec, 'filename_glob'):
                full_glob = os.path.join(self._config.settings.work_dir,
                                         group_sec.filename_glob)
                filenames = sorted(glob(full_glob))
                for filename in filenames:
                    node = self._create_node(filename, group)
            elif hasattr(group_sec, 'from_group'):
                from_group = self.groups[group_sec.from_group]
                process_name = group_sec.process
                process = process_classes[process_name]()
                for node in from_group.nodes:
                    # TODO: Make smarter.
                    fn = self._get_converted_filename(node.filename)
                    next_node = self._create_node(fn, group, process_name)
                    self._link_nodes(node, next_node)
            elif hasattr(group_sec, 'nodes'):
                for node_name in map(str.strip, group_sec.nodes.split(',')):
                    node_sec = getattr(self._config, node_name)
                    from_group = self.groups[node_sec.from_group]
                    process = process_classes[node_sec.process]()
                    fn_args = [group_name, node_name,
                               node_sec.process]
                    fn = self._rm.get_filename(fn_args, out_ext=process.out_ext)
                    if hasattr(node_sec, 'section') and hasattr(node_sec, 'item'):
                        next_node = self._create_node(fn, group, 
                                                      node_sec.process, 
                                                      node_sec.section, 
                                                      node_sec.item)
                    else:
                        next_node = self._create_node(fn, group, 
                                                      node_sec.process)
                    for node in from_group.nodes:
                        self._link_nodes(node, next_node)
        self._check_nodes()


    def print_nodes(self):
        for batchname, batch in self.batches.items():
            print(batchname)
            for group in batch:
                print('  ' + group.__repr__())
                for node in group.nodes:
                    print('    ' + node.__repr__())
        print('')

    def _create_node(self, filename, group, process_name=None, 
                     section=None, item=None):
        node = Node(filename, self)
        node.process_name = process_name
        node.section = section
        node.item = item
        self.nodes.append(node)
        self.group = group
        group.nodes.append(node)
        return node

    def _create_group(self, name, batch):
        group = Group(name, self)
        self.groups[name] = group
        if batch not in self.batches:
            self.batches[batch] = []
        self.batches[batch].append(group)
        return group

    def _link_nodes(self, start_node, end_node):
        start_node.to_nodes.append(end_node)
        end_node.from_nodes.append(start_node)

    def _check_nodes(self):
        warnings = []
        init_groups = self.batches['batch0']
        for group in init_groups:
            for node in group.nodes:
                if not node.exists():
                    msg = 'initial node {} does not exist'.format(node)
                    warnings.append(msg)
        for warning in warnings:
            print(warning)

    def _get_converted_filename(self, conv_filename):
        pre, ext = os.path.splitext(conv_filename)
        if ext[:3] != self._config.convert.convert_from:
            msg = 'File extension {} != {}'.format(ext[:3], 
                    self._config.convert.convert_from)
            raise Exception(msg)

        return pre + '.' + ext[-1] + self._config.convert.convert_to 


class Group(object):
    def __init__(self, name, dag):
        self.name = name
        self.dag = dag
        self.nodes = []

    def __repr__(self):
        return '<Group {} ({} nodes)>'.format(self.name, len(self.nodes))


class Node(object):
    def __init__(self, filename, dag):
        self.filename = filename
        self.dag = dag
        self.from_nodes = []
        self.to_nodes = []
        self.group = None

    def exists(self):
        return os.path.exists(self.filename) and os.path.exists(self.filename + '.done')

    def is_start(self):
        return not len(self.from_nodes)

    def is_end(self):
        return not len(self.to_nodes)
    
    def __repr__(self):
        basename = os.path.basename(self.filename)
        exists = 'X' if self.exists() else ' '

        return '<Node {} [{}]>'.format(basename, exists)


def create_node_dag(args, config):
    rm = ResultsManager(config)
    dag = NodeDAG(args, config, rm)

    group_names = config.groups.options()
    dag.generate_all_nodes(group_names)
    return dag


def create_dummy_node_dag(args, config):
    rm = ResultsManager(config)
    dag = NodeDAG(args, config, rm)
    # Initial files for conversion.
    groups_names = [
        ('pp1', ['atmos.000.pp1', 'atmos.006.pp1', 'atmos.012.pp1']), 
        ('pp2', ['atmos.000.pp2', 'atmos.006.pp2', 'atmos.012.pp2']),
        ]

    dag.generate_all_nodes(groups_names)
    return dag
