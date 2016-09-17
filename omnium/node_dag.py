from __future__ import print_function
import os
from collections import OrderedDict
from glob import glob
from logging import getLogger

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Computer, Batch, Group, Node

logger = getLogger('omni')


class NodeDAG(object):
    SAVE_FILE_TPL = '{}.{}'

    @staticmethod
    def regenerate(config, process_classes):
        if os.path.exists('.omni/sqlite3.db'):
            os.remove('.omni/sqlite3.db')
        return NodeDAG.generate(config, process_classes)

    @staticmethod
    def generate(config, process_classes):
        if not os.path.exists('.omni'):
            os.makedirs('.omni')

        dag = NodeDAG(config, process_classes, None)

        group_names = config['groups'].keys()
        dag.generate_all_nodes(group_names)
        dag.log_nodes()
        return dag

    def __init__(self, config, process_classes, remote_computer_name=None):
        self.config = config
        self.process_classes = process_classes

        self.remote_computer_name = remote_computer_name
        self._set_computer_name()
        self._connect_create_db()

    def render(self, filename='node_dag.png', display=True):
        import pygraphviz as pgv
        import subprocess as sp

        G = pgv.AGraph(directed=True, rank='same', rankdir='LR')
        init_batch = self.get_batches()[0]
        next_nodes = {}
        for group in init_batch.groups:
            for node in group.nodes:
                next_nodes[node.id] = node

        while next_nodes:
            new_next_nodes = {}
            for n in next_nodes.values():
                G.add_node('{}:{}'.format(n.id, n.name))

                for nn in n.to_nodes:
                    if nn.id not in new_next_nodes:
                        new_next_nodes[nn.id] = nn
                    G.add_edge('{}:{}'.format(n.id, n.name),
                               '{}:{}'.format(nn.id, nn.name))
            next_nodes = new_next_nodes
        G.layout('dot')
        G.draw(filename)
        logger.info('Node Directed Acyclic Graph rendered to {}'.format(filename))
        if display:
            cmd = 'eog {}'.format(filename)
            try:
                sp.call(cmd.split())
            except sp.CalledProcessError as ex:
                logger.warn('Problem running {}'.format(cmd))
                logger.warn('eog not installed?')

    def generate_all_nodes(self, group_names):
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

        for batch_name in self.config['batches'].keys():
            batch_sec = self.config['batches'][batch_name]
            batch = Batch(name=batch_name, index=batch_sec['index'])
            self._session.add(batch)

        completed_groups = []
        incomplete_groups = []
        node_process_groups = []
        for group_name in group_names:
            group_sec = self.config['groups'][group_name]

            batch = self.get_batch(group_sec['batch'])

            base_dirname = group_sec['base_dir']
            group = Group(name=group_name,
                          batch=batch,
                          base_dirname=base_dirname)
            self._session.add(group)

            group_type = group_sec['type']
            if group_type == 'init':
                self._generate_init_nodes(group, group_sec)
                completed_groups.append(group)
            elif group_type == 'group_process':
                self._generate_group_process_nodes(group, group_sec)
                incomplete_groups.append(group)
            elif group_type == 'nodes_process':
                self._generate_nodes_process_nodes(group, group_sec)
                node_process_groups.append(group)
                completed_groups.append(group)

        # Not necessary, but help debug if somethings goes wrong.
        self.commit()

        # Work out group processing order:
        group_processing = []
        while incomplete_groups:
            for group in incomplete_groups:
                group_sec = self.config['groups'][group.name]
                from_group = self.get_group(group_sec['from_group'])
                if from_group in completed_groups:
                    group_processing.append(group)
                    completed_groups.append(group)
                    incomplete_groups.remove(group)

        # Hook up group_processing nodes.
        for group in group_processing:
            group_sec = self.config['groups'][group.name]

            group_type = group_sec['type']
            from_group = self.get_group(group_sec['from_group'])
            for from_node in from_group.nodes:
                process_name = group_sec['process']
                orig_filename = from_node.filename(self.config)

                process = self.process_classes[process_name]
                new_filename = process.convert_filename(orig_filename)

                node = self._create_node(new_filename,
                                         group,
                                         process_name=process_name)
                node.from_nodes.append(from_node)
        # Not necessary, but help debug if somethings goes wrong.
        self.commit()

        # Hook up remaining nodes.
        for group in node_process_groups:
            group_sec = self.config['groups'][group.name]
            for node_name in group_sec['nodes']:
                node = self.get_node(node_name)
                node_sec = self.config['nodes'][node_name]
                if 'from_group' in node_sec:
                    from_group = self.get_group(node_sec['from_group'])
                    for from_node in from_group.nodes:
                        node.from_nodes.append(from_node)
                else:
                    if 'from_node' in node_sec:
                        from_nodes = [node_sec['from_node']]
                    else:
                        from_nodes = node_sec['from_nodes']

                    logger.debug(node)
                    for from_node_name in from_nodes:
                        logger.debug(from_node_name)
                        from_node = self.get_node(from_node_name)
                        node.from_nodes.append(from_node)

        self.commit()
        # Make sure all statuses are set correctly.
        logger.debug('settings all statuses')
        self.verify_status(update=True)

    def _show_nodes(self, printer):
        for batch in self._session.query(Batch).all():
            printer(batch.__repr__())
            for group in batch.groups:
                printer('  ' + group.__repr__())
                for node in group.nodes:
                    printer('    ' + node.__repr__())
        printer('')

    def print_nodes(self):
        self._show_nodes(print)

    def log_nodes(self):
        self._show_nodes(logger.debug)

    def get_proc(self, node_name):
        node = self.get_node(node_name)
        return self.process_classes[node.process](self.config, node)

    def commit(self):
        self._session.commit()

    def get_computers(self):
        return self._session.query(Computer).all()

    def get_batches(self):
        return self._session.query(Batch).order_by(Batch.index)

    def get_batch(self, batch_name):
        return self._session.query(Batch)\
                   .filter_by(name=batch_name).one()

    def get_group(self, group_name):
        return self._session.query(Group)\
                   .filter_by(name=group_name).one()

    def get_node(self, node_name, group_name=None):
        query = self._session.query(Node)\
                    .filter_by(name=node_name)
        if group_name:
            query = query.join(Group).filter_by(name=group_name)
        return query.one()

    def get_node_from_id(self, node_id):
        query = self._session.query(Node)\
                    .filter_by(id=node_id)
        return query.one()

    def get_nodes(self, node_name):
        query = self._session.query(Node)\
                    .filter_by(name=node_name)
        return query.all()

    def _verify_node(self, node, update):
        filename = node.filename(self.config)
        status = self._get_node_status(filename)
        if node.status != status:
            logger.debug('{}: {} doesn\'t match {}'.format(node,
                                                           node.status,
                                                           status))
            if update:
                node.status = status
                logger.debug('Updated: {}'.format(node))
            return status, [(node, status)]
        return status, []

    def _verify_group_batch(self, statuses, group_batch, update):
        if len(statuses) == 1:
            new_status = statuses.pop()
        else:
            new_status = 'incomplete'
        if group_batch.status != new_status:
            logger.debug('{}: {} doesn\'t match {}'.format(group_batch,
                                                           group_batch.status,
                                                           new_status))
            if update:
                group_batch.status = new_status
                logger.debug('Updated: {}'.format(group_batch))
            return new_status, [(group_batch, new_status)]
        return new_status, []

    def verify_status(self, update):
        errors = []
        for batch in self.get_batches():
            group_statuses = set()
            for group in batch.groups:
                node_statuses = set()
                for node in group.nodes:
                    node_status, node_errors = self._verify_node(node, update)
                    errors.extend(node_errors)
                    node_statuses |= {node_status}
                group_status, group_error = self._verify_group_batch(node_statuses,
                                                                     group, update)
                errors.extend(group_error)
                group_statuses |= {group_status}
            batch_status, batch_error = self._verify_group_batch(group_statuses,
                                                                 batch, update)
            errors.extend(batch_error)

        if len(errors):
            if update:
                logger.debug('Updating DAG')
                self.commit()
                logger.info('Updated DAG')
            else:
                msg = 'Status doesn\'t match for {} node(s)/group(s)/batch(es)\n'\
                      'To fix run:\nomni verify-node-graph --update'\
                      .format(len(errors))
                raise Exception(msg)
        else:
            logger.info('All nodes statuses verified')

    def _set_computer_name(self):
        self.computer_name = self.config['computer_name']

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

    def _get_node_status(self, filename):
        status = 'missing'
        if os.path.exists(filename):
            if os.path.exists(filename + '.done'):
                status = 'done'
            else:
                status = 'processing'
        return status

    def _get_base_dir(self, base_dirname):
        comp_sec = self.config['computers'][self.computer_name]
        base_dir = comp_sec['dirs'][base_dirname]
        return base_dir

    def _generate_init_nodes(self, group, group_sec):
        base_dir = self._get_base_dir(group.base_dirname)
        full_glob = os.path.join(base_dir,
                                 group_sec['filename_glob'])
        logger.debug('Using filename glob: {}'.format(full_glob))
        filenames = sorted(glob(full_glob))
        if not len(filenames):
            logger.warn('No filenames for {} using:'.format(group))
            logger.warn(full_glob)

        for filename in filenames:
            rel_filename = os.path.relpath(filename, base_dir)
            node = self._create_node(rel_filename, group)

    def _generate_group_process_nodes(self, group, group_sec):
        process_name = group_sec['process']
        process = self.process_classes[process_name](self.config,
                                                     self.computer_name)

    def _get_filename(self, results_dir, node_name, out_ext):
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)

        save_file = os.path.join(results_dir,
                                 self.SAVE_FILE_TPL.format(node_name, out_ext))
        return save_file

    def _generate_from_group_nodes(self, group, node_name, node_sec):
        from_group = self.get_group(node_sec['from_group'])
        process = self.process_classes[node_sec['process']](self.config,
                                                            self.computer_name)
        base_dir = self._get_base_dir(group.base_dirname)
        filename = self._get_filename(base_dir, node_name, out_ext=process.out_ext)
        rel_filename = os.path.relpath(filename, base_dir)
        if 'variable' in node_sec:
            var_sec = self.config['variables'][node_sec['variable']]
            next_node = self._create_node(rel_filename, group,
                                          node_name,
                                          node_sec['process'],
                                          var_sec['section'],
                                          var_sec['item'])
        else:
            next_node = self._create_node(rel_filename, group,
                                          node_name,
                                          node_sec['process'])

    def _generate_from_nodes_nodes(self, group, node_name, node_sec):
        process = self.process_classes[node_sec['process']](self.config,
                                                            self.computer_name)
        base_dir = self._get_base_dir(group.base_dirname)
        filename = self._get_filename(base_dir, node_name, out_ext=process.out_ext)
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

    def _generate_nodes_process_nodes(self, group, group_sec):
        for node_name in group_sec['nodes']:
            node_sec = self.config['nodes'][node_name]

            if 'from_group' in node_sec:
                self._generate_from_group_nodes(group, node_name, node_sec)
            elif 'from_nodes' in node_sec:
                self._generate_from_nodes_nodes(group, node_name, node_sec)
            elif 'from_node' in node_sec:
                self._generate_from_nodes_nodes(group, node_name, node_sec)

    def _create_node(self, rel_filename, group, name=None, process_name=None,
                     section=None, item=None):
        logger.debug('creating node {}: {}'.format(name, rel_filename))
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
