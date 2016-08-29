import os
from collections import OrderedDict
from glob import glob

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from results import ResultsManager
from omnium.processes import get_process_classes
from models import Base, Computer, Batch, Group, Node

class NodeDAG(object):
    def __init__(self, args, config, rm, remote_computer_name):
        self._args = args
        self._config = config
        self._rm = rm
        self.remote_computer_name = remote_computer_name
        self._connect_create_db()

    def _connect_create_db(self):
        if not os.path.exists('.omni'):
            os.makedirs('.omni')
        if not self.remote_computer_name:
            engine = create_engine('sqlite:///.omni/sqlite3.db')
            Base.metadata.create_all(engine)
        else:
            engine = create_engine('sqlite:///.omni/{}_sqlite3.db'.format(self.remote_computer_name))

        Session = sessionmaker(bind=engine)
        self._session = Session()

    def commit(self):
        self._session.commit()

    def get_group(self, group_name):
        return self._session.query(Group).filter_by(name=group_name).one()

    def get_node(self, node_name):
        return self._session.query(Node).filter_by(name=node_name).one()

    def get_batch(self, batch_name):
        return self._session.query(Batch).filter_by(name=batch_name).one()

    def _get_node_status(self, filename):
        status = 'missing'
        if os.path.exists(filename):
            if os.path.exists(filename + '.done'):
                status = 'done'
            else:
                status = 'processing'
        return status

    def verify_status(self):
        self.errors = []
        computer_name = open(self._config['computers']['current'], 'r').read().strip()
        for node in self._session.query(Node).all():
            status = self._get_node_status(node.filename(computer_name, self._config))
            if node.status != status:
                self.errors.append((node, status))
                print('{}: {} doesn\'t match {}'.format(node.name,
                                                        node.status,
                                                        status))
                if self._args.update:
                    node.status = status
                    print('Updated: {}'.format(node))

        if len(self.errors):
            if self._args.update:
                self.commit()
                self.errors = []
            else:
                msg = 'Status doesn\'t match for {} node(s)\n'\
                      'To fix run:\nomni verify-node-graph --update'\
                      .format(len(self.errors))
                raise Exception(msg)
        else:
            print('All nodes statuses verified')

    def generate_all_nodes(self, group_names):
        # TODO: Messy function. Split into easier to manage functions.
        process_classes = get_process_classes(self._args.cwd)
        # TODO:
        # Test to see if entry for this comp already exists.
        # Raise error if so.
        #try:
            #self._session.query(Computer).filter_by(name='zg').one()
        if not self.remote_computer_name:
            if 'current' in self._config['computers']:
                computer_name = open(self._config['computers']['current'], 'r').read().strip()
            else:
                raise Exception('Not sure what computer this is running on')
        else:
            raise Exception('remote_computer_name should be None')
        computer = Computer(name=computer_name)
        self._session.add(computer)

        for i, group_name in enumerate(group_names):
            batch = Batch(name='batch{}'.format(i))
            self._session.add(batch)

            group_sec = self._config['groups'][group_name]
            base_dirname = group_sec['base_dir']
            group = Group(name=group_name, batch=batch, base_dirname=base_dirname)
            self._session.add(group)

            if 'filename_glob' in group_sec:
                base_dir = self._config['computers'][computer_name]['dirs'][base_dirname]
                full_glob = os.path.join(base_dir,
                                         group_sec['filename_glob'])
                filenames = sorted(glob(full_glob))
                for filename in filenames:
                    rel_filename = os.path.relpath(filename, base_dir)
                    node = self._create_node(base_dir, rel_filename, group)
            elif 'from_group' in group_sec:
                from_group = self.get_group(group_sec['from_group'])
                process_name = group_sec['process']
                process = process_classes[node_sec['process']](self._args, self._config, computer_name)
                for node in from_group.nodes:
                    # TODO: Make smarter.
                    filename = self._get_converted_filename(node.filename(computer_name, self._config))
                    rel_filename = os.path.relpath(filename, base_dir)
                    next_node = self._create_node(base_dir, rel_filename, group, process_name=process_name)
                    next_node.from_nodes.append(node)
            elif 'nodes' in group_sec :
                for node_name in group_sec['nodes']:
                    node_sec = self._config['nodes'][node_name]
                    if 'from_group' in node_sec:
                        from_group = self.get_group(node_sec['from_group'])
                        process = process_classes[node_sec['process']](self._args, self._config, computer_name)
                        fn_args = [group_name, node_name,
                                   node_sec['process']]
                        filename = self._rm.get_filename(fn_args, out_ext=process.out_ext)
                        if 'variable' in node_sec:
                            var_sec = self._config['variables'][node_sec['variable']]
                            rel_filename = os.path.relpath(filename, base_dir)
                            next_node = self._create_node(base_dir, rel_filename, group, 
                                                          node_name,
                                                          node_sec['process'], 
                                                          var_sec.as_int('section'), 
                                                          var_sec.as_int('item'))
                        else:
                            rel_filename = os.path.relpath(filename, base_dir)
                            next_node = self._create_node(base_dir, rel_filename, group, 
                                                          node_name,
                                                          node_sec['process'])
                        for node in from_group.nodes:
                            next_node.from_nodes.append(node)
                    elif 'from_nodes' in node_sec:
                        process = process_classes[node_sec['process']](self._args, self._config, computer_name)
                        fn_args = [group_name, node_name,
                                   node_sec['process']]
                        filename = self._rm.get_filename(fn_args, out_ext=process.out_ext)
                        if 'section' in node_sec and 'item' in node_sec:
                            rel_filename = os.path.relpath(filename, base_dir)
                            next_node = self._create_node(base_dir, rel_filename, group, 
                                                          node_name,
                                                          process_name=node_sec['process'], 
                                                          section=node_sec['section'], 
                                                          item=node_sec['item'])
                        else:
                            rel_filename = os.path.relpath(filename, base_dir)
                            next_node = self._create_node(base_dir, rel_filename, group, 
                                                          process_name=node_sec['process'])
                        from_nodes = node_sec['from_nodes']
                        for from_node_name in from_nodes:
                            from_node = self.get_node(from_node_name)
                            next_node.from_nodes.append(from_node)

                    elif 'from_node' in node_sec:
                        from_node = self.get_node(node_sec['from_node'])
                        process = process_classes[node_sec['process']](self._args, self._config, computer_name)
                        fn_args = [group_name, node_name,
                                   node_sec['process']]
                        filename = self._rm.get_filename(fn_args, out_ext=process.out_ext)
                        if 'section' in node_sec and 'item' in node_sec:
                            rel_filename = os.path.relpath(filename, base_dir)
                            next_node = self._create_node(base_dir, rel_filename, group, 
                                                          process_name=node_sec['process'], 
                                                          section=node_sec['section'], 
                                                          item=node_sec['item'])
                        else:
                            rel_filename = os.path.relpath(filename, base_dir)
                            next_node = self._create_node(base_dir, rel_filename, group, 
                                                          process_name=node_sec['process'])
                        for node in from_group.nodes:
                            next_node.from_nodes.append(node)
        #self._check_nodes()
        self._session.commit()


    def print_nodes(self):
        for batch in self._session.query(Batch).all():
            print(batch.__repr__())
            for group in batch.groups:
                print('  ' + group.__repr__())
                for node in group.nodes:
                    print('    ' + node.__repr__())
        print('')

    def _create_node(self, base_dir, rel_filename, group, name=None, process_name=None, 
                     section=None, item=None):
        status = self._get_node_status(os.path.join(base_dir, rel_filename))
        if not name:
            name = os.path.basename(rel_filename)
        node = Node(name=name, 
                    rel_filename=rel_filename,
                    process=process_name,
                    status=status,
                    section=section,
                    item=item,
                    group=group)

        self._session.add(node)
        return node

    def _create_group(self, name, batch, base_dirname):
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
        conv_config = self._config['process_options']['convert_pp_to_nc']
        if ext[:3] != conv_config['convert_from']:
            msg = 'File extension {} != {}'.format(ext[:3], 
                    conv_config['convert_from'])
            raise Exception(msg)

        return pre + '.' + ext[-1] + conv_config['convert_to'] 


def regenerate_node_dag(args, config):
    os.remove('.omni/sqlite3.db')
    return generate_node_dag(args, config)


def generate_node_dag(args, config):
    computer_name = open(config['computers']['current'], 'r').read().strip()
    rm = ResultsManager(computer_name, config)
    dag = NodeDAG(args, config, rm, None)

    group_names = config['groups'].keys()
    dag.generate_all_nodes(group_names)
    return dag


def get_node_dag(args, config, remote_computer_name=None):
    computer_name = open(config['computers']['current'], 'r').read().strip()
    rm = ResultsManager(computer_name, config)
    dag = NodeDAG(args, config, rm, remote_computer_name)
    return dag


def create_dummy_node_dag(args, config):
    computer_name = open(config['computers']['current'], 'r').read().strip()
    rm = ResultsManager(computer_name, config)
    dag = NodeDAG(args, config, rm)
    # Initial files for conversion.
    groups_names = [
        ('pp1', ['atmos.000.pp1', 'atmos.006.pp1', 'atmos.012.pp1']), 
        ('pp2', ['atmos.000.pp2', 'atmos.006.pp2', 'atmos.012.pp2']),
        ]

    dag.generate_all_nodes(groups_names)
    return dag
