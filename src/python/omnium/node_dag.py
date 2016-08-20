import os
from collections import OrderedDict
from glob import glob

from results import ResultsManager

class NodeDAG(object):
    def __init__(self, args, config, rm):
        self._args = args
        self._config = config
        self._rm = rm

        self.nodes = []
        self.groups = OrderedDict()
        self.batches = OrderedDict()

    def generate_all_nodes(self, groups_names):
        self._generate_conversion_nodes(groups_names)

        self._generate_process_nodes()

        self._check_nodes()


    def print_nodes(self):
        print('batch1')
        for group in self.batches['batch1']:
            print('  ' + group.__repr__())
            for node in group.nodes:
                print('    ' + node.__repr__())
        print('')
        print('batch2')
        for group in self.batches['batch2']:
            print('  ' + group.__repr__())
            for node in group.nodes:
                print('    ' + node.__repr__())
        print('')
        print('batch3')
        for group in self.batches['batch3']:
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

    def _generate_conversion_nodes(self, groups_names):
        for group_name, conv_filenames in groups_names:
            group = self._create_group(group_name, 'batch1')

            convert_from = self._config.convert.convert_from[1:]
            convert_to = self._config.convert.convert_to[1:]

            next_group_name = group.name.replace(convert_from, convert_to)
            next_group = self._create_group(next_group_name, 'batch2')

            for conv_filename in conv_filenames:
                output_filename = self._get_converted_filename(conv_filename)

                start_node = self._create_node(conv_filename, group)
                next_node = self._create_node(output_filename, 
                                              next_group, 'convert_pp_to_nc')
                self._link_nodes(start_node, next_node)

    def _generate_process_nodes(self):
        for output_var in self._config.output_vars.options():
            sec = getattr(self._config, output_var)
            group = self.groups[sec.group]

            proc_group_name = '{}_{}'.format(output_var, group.name)
            proc_group = self._create_group(proc_group_name, 'batch3')

            fn_args = [sec.process, sec.section, sec.item]
            fn_args.extend([n.filename for n in group.nodes])
            fn = self._rm.get_filename(fn_args)
            node = self._create_node(fn, proc_group, sec.process, 
                                     sec.section, sec.item)
            for from_node in group.nodes:
                self._link_nodes(from_node, node)

    def _check_nodes(self):
        warnings = []
        init_groups = self.batches['batch1']
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

    groups_names = []
    for opt in config.convert_groups.options():
        file_glob = getattr(config.convert_groups, opt)

        full_glob = os.path.join(config.settings.work_dir, file_glob)
        filenames = sorted(glob(full_glob))
        groups_names.append((opt[5:], filenames))

    dag.generate_all_nodes(groups_names)
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
