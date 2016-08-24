import os
from collections import OrderedDict
from glob import glob

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from results import ResultsManager
from omnium.processes import get_process_classes
from models import Base, Computer, Batch, Group, Node

engine = create_engine('sqlite:///.omni/sqlite3.db')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

class NodeDAG(object):
    def __init__(self, args, config, rm):
        self._session = Session()
        self._args = args
        self._config = config
        self._rm = rm


    def commit(self):
        self._session.commit()

    def get_group(self, group_name):
        return self._session.query(Group).filter_by(name=group_name).one()

    def get_batch(self, batch_name):
        return self._session.query(Batch).filter_by(name=batch_name).one()

    def generate_all_nodes(self, group_names):
        process_classes = get_process_classes(self._args.cwd)
        computer = Computer(name='zg')
        self._session.add(computer)

        for i, group_name in enumerate(group_names):
            batch = Batch(name='batch{}'.format(i))
            self._session.add(batch)

            group_sec = getattr(self._config, group_name)
            group = Group(name=group_name, batch=batch)
            self._session.add(group)

            if hasattr(group_sec, 'filename_glob'):
                full_glob = os.path.join(self._config.settings.work_dir,
                                         group_sec.filename_glob)
                filenames = sorted(glob(full_glob))
                for filename in filenames:
                    node = self._create_node(filename, group)
            elif hasattr(group_sec, 'from_group'):
                from_group = self.get_group(group_sec.from_group)
                process_name = group_sec.process
                process = process_classes[process_name]()
                for node in from_group.nodes:
                    # TODO: Make smarter.
                    fn = self._get_converted_filename(node.filename)
                    next_node = self._create_node(fn, group, process_name)
                    next_node.from_nodes.append(node)
            elif hasattr(group_sec, 'nodes'):
                for node_name in map(str.strip, group_sec.nodes.split(',')):
                    node_sec = getattr(self._config, node_name)
                    from_group = self.get_group(node_sec.from_group)
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
                        next_node.from_nodes.append(node)
        #self._check_nodes()
        self._session.commit()


    def print_nodes(self):
        for batch in self._session.query(Batch).all():
            print(batch.name)
            for group in batch.groups:
                print('  ' + group.__repr__())
                for node in group.nodes:
                    print('    ' + node.__repr__())
        print('')

    def _create_node(self, filename, group, process_name=None, 
                     section=None, item=None):
        status = 'missing'
        if os.path.exists(filename):
            if os.path.exists(filename + '.done'):
                status = 'done'
            else:
                status = 'processing'
        node = Node(name=os.path.basename(filename), 
                    filename=filename,
                    process=process_name,
                    status=status,
                    section=section,
                    item=item,
                    group=group)

        self._session.add(node)
        return node

    def _create_group(self, name, batch):
        group = Group(name=name, batch=batch)
        self._session.add(group)
        return group

    def _check_nodes(self):
        warnings = []
        batch = self.get_batch('batch0')
        for group in batch.groups:
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


if False:
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


def generate_node_dag(args, config):
    rm = ResultsManager(config)
    dag = NodeDAG(args, config, rm)

    group_names = config.groups.options()
    dag.generate_all_nodes(group_names)
    return dag


def get_node_dag(args, config):
    rm = ResultsManager(config)
    dag = NodeDAG(args, config, rm)
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
