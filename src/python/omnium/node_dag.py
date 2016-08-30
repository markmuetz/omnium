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
        self._set_computer_name()
        self._connect_create_db()

    def _set_computer_name(self):
        if 'current' in self._config['computers']:
            computer_txt = self._config['computers']['current']
            self.computer_name = open(computer_txt, 'r').read().strip()
        else:
            raise Exception('Not sure what computer this is running on')


    def _connect_create_db(self):
        if not os.path.exists('.omni'):
            os.makedirs('.omni')

        if not self.remote_computer_name:
            connection_string = 'sqlite:///.omni/sqlite3.db'
            engine = create_engine(connection_string)
            Base.metadata.create_all(engine)
        else:
            connection_string = 'sqlite:///.omni/{}_sqlite3.db'\
                                .format(self.remote_computer_name)
            engine = create_engine(connection_string)

        Session = sessionmaker(bind=engine)
        self._session = Session()

    def commit(self):
        self._session.commit()

    def get_group(self, group_name):
        return self._session.query(Group)\
                   .filter_by(name=group_name).one()

    def get_node(self, node_name):
        return self._session.query(Node)\
                   .filter_by(name=node_name).one()

    def get_batch(self, batch_name):
        return self._session.query(Batch)\
                   .filter_by(name=batch_name).one()

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
        for node in self._session.query(Node).all():
            filename = node.filename(self.computer_name, self._config)
            status = self._get_node_status(filename)
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


    def _get_base_dir(self, base_dirname):
        base_dir = self._config['computers'][self.computer_name]\
                               ['dirs'][base_dirname]
        return base_dir

    def _generate_init_nodes(self, group, group_sec):
        base_dir = self._get_base_dir(group.base_dirname)
        full_glob = os.path.join(base_dir,
                                 group_sec['filename_glob'])
        filenames = sorted(glob(full_glob))
        for filename in filenames:
            rel_filename = os.path.relpath(filename, base_dir)
            node = self._create_node(rel_filename, group)

    def _generate_group_process_nodes(self, group, group_sec):
        from_group = self.get_group(group_sec['from_group'])
        process_name = group_sec['process']
        process = self.process_classes[process_name](self._args, 
                                                     self._config, 
                                                     self.computer_name)
        for node in from_group.nodes:
            # TODO: Make smarter.
            orig_filename = node.filename(self.computer_name, self._config)
            filename = self._get_converted_filename(orig_filename)
            base_dir = self._get_base_dir(group.base_dirname)
            rel_filename = os.path.relpath(filename, base_dir)
            next_node = self._create_node(rel_filename, 
                                          group, 
                                          process_name=process_name)
            next_node.from_nodes.append(node)


    def _generate_from_group_nodes(self, group, node_name, node_sec):
        from_group = self.get_group(node_sec['from_group'])
        process = self.process_classes[node_sec['process']](self._args, 
                                                            self._config, 
                                                            self.computer_name)
        fn_args = [from_group.name, node_name,
                   node_sec['process']]
        base_dir = self._get_base_dir(group.base_dirname)
        filename = self._rm.get_filename(base_dir, node_name, out_ext=process.out_ext)
        rel_filename = os.path.relpath(filename, base_dir)
        if 'variable' in node_sec:
            var_sec = self._config['variables'][node_sec['variable']]
            next_node = self._create_node(rel_filename, group, 
                                          node_name,
                                          node_sec['process'], 
                                          var_sec.as_int('section'), 
                                          var_sec.as_int('item'))
        else:
            next_node = self._create_node(rel_filename, group, 
                                          node_name,
                                          node_sec['process'])
        for node in from_group.nodes:
            next_node.from_nodes.append(node)


    def _generate_from_nodes_nodes(self, group, node_name, node_sec, from_nodes):
        process = self.process_classes[node_sec['process']](self._args, 
                                                            self._config, 
                                                            self.computer_name)
        fn_args = [group.name, node_name,
                   node_sec['process']]
        base_dir = self._get_base_dir(group.base_dirname)
        filename = self._rm.get_filename(base_dir, node_name, out_ext=process.out_ext)
        rel_filename = os.path.relpath(filename, base_dir)
        if 'section' in node_sec and 'item' in node_sec:
            next_node = self._create_node(rel_filename, group, 
                                          node_name,
                                          process_name=node_sec['process'], 
                                          section=node_sec['section'], 
                                          item=node_sec['item'])
        else:
            next_node = self._create_node(rel_filename, group, 
					  node_name,
                                          process_name=node_sec['process'])
        for from_node_name in from_nodes:
            from_node = self.get_node(from_node_name)
            next_node.from_nodes.append(from_node)


    def _generate_nodes_process_nodes(self, group, group_sec):
        for node_name in group_sec['nodes']:
            node_sec = self._config['nodes'][node_name]

            if 'from_group' in node_sec:
                self._generate_from_group_nodes(group, node_name, node_sec)
            elif 'from_nodes' in node_sec:
                from_nodes = node_sec['from_nodes']
                self._generate_from_nodes_nodes(group, node_name, 
                                                node_sec, from_nodes)
            elif 'from_node' in node_sec:
                from_nodes = [node_sec['from_node']]
                self._generate_from_nodes_nodes(group, node_name, 
                                                node_sec, from_nodes)

    def generate_all_nodes(self, group_names):
        self.process_classes = get_process_classes(self._args.cwd)

        computer_count = self._session.query(Computer)\
                             .filter_by(name=self.computer_name).count()
        if computer_count:
            msg = 'Computer {} already exists in DB\n'\
                  'Perhaps you should run:\n'\
                  'omni gen-node-graph --regen'\
                  .format(self.computer_name)
            raise Exception(msg)

        if self.remote_computer_name:
            raise Exception('remote_computer_name should be None')

        computer = Computer(name=self.computer_name)
        self._session.add(computer)

        for batch_name in self._config['batches'].keys():
            batch_sec = self._config['batches'][batch_name]
            batch = Batch(name=batch_name, index=batch_sec['index'])
            self._session.add(batch)

        for group_name in group_names:
            group_sec = self._config['groups'][group_name]

            batch = self.get_batch(group_sec['batch'])

            base_dirname = group_sec['base_dir']
            group = Group(name=group_name, 
                          batch=batch, 
                          base_dirname=base_dirname)
            self._session.add(group)

            group_type = group_sec['type']
            if group_type == 'init':
                self._generate_init_nodes(group, group_sec) 
            elif group_type == 'group_process':
                self._generate_group_process_nodes(group, group_sec)
            elif group_type == 'nodes_process':
                self._generate_nodes_process_nodes(group, group_sec)
        self._session.commit()


    def print_nodes(self):
        for batch in self._session.query(Batch).all():
            print(batch.__repr__())
            for group in batch.groups:
                print('  ' + group.__repr__())
                for node in group.nodes:
                    print('    ' + node.__repr__())
        print('')

    def _create_node(self, rel_filename, group, name=None, process_name=None, 
                     section=None, item=None):
        base_dir = self._get_base_dir(group.base_dirname)
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

    def _get_converted_filename(self, conv_filename):
        pre, ext = os.path.splitext(conv_filename)
        conv_config = self._config['process_options']['convert_pp_to_nc']
        if ext[:3] != conv_config['convert_from']:
            msg = 'File extension {} != {}'.format(ext[:3], 
                    conv_config['convert_from'])
            raise Exception(msg)

        return pre + '.' + ext[-1] + conv_config['convert_to'] 


def regenerate_node_dag(args, config):
    if os.path.exists('.omni/sqlite3.db'):
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
