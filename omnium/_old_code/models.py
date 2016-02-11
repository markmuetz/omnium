import os
import re

from sqlalchemy import Integer, ForeignKey, String, Column, Table, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()

node_to_node = Table("node_to_node", Base.metadata,
                     Column("from_node_id", Integer, ForeignKey("nodes.id"), primary_key=True),
                     Column("to_node_id", Integer, ForeignKey("nodes.id"), primary_key=True)
                     )

statuses = Enum('missing', 'processing', 'incomplete', 'done', name='statuses')


class Computer(Base):
    __tablename__ = 'computers'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    batches = relationship('Batch', backref='computer')

    def __repr__(self):
        return '<Computer {} (id={})>'.format(self.name, self.id)


class Batch(Base):
    __tablename__ = 'batches'

    id = Column(Integer, primary_key=True)
    index = Column(Integer)
    name = Column(String)
    computer_id = Column(Integer, ForeignKey('computers.id'))
    status = Column(statuses)

    groups = relationship('Group', backref='batch')

    def __repr__(self):
        return '<Batch {} (id={}, status={})>'\
               .format(self.name, self.id, self.status)


class Group(Base):
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    status = Column(statuses)
    base_dirname = Column(String)

    batch_id = Column(Integer, ForeignKey('batches.id'))
    nodes = relationship('Node', backref='group')

    def __repr__(self):
        return '<Group {} (id={}, status={})>'\
               .format(self.name, self.id, self.status)


class Node(Base):
    __tablename__ = 'nodes'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    rel_filename = Column(String)
    process = Column(String)
    status = Column(statuses)
    section = Column(Integer)
    item = Column(Integer)

    group_id = Column(Integer, ForeignKey('groups.id'))
    to_nodes = relationship("Node",
                            secondary=node_to_node,
                            primaryjoin=id == node_to_node.c.from_node_id,
                            secondaryjoin=id == node_to_node.c.to_node_id,
                            backref="from_nodes"
                            )

    def filename(self, config, computer_name=None):
        if not computer_name:
            computer_name = config['computer_name']
        base_dir = config['computers'][computer_name]['dirs'][self.group.base_dirname]
        return os.path.join(base_dir, self.rel_filename)

    def node_type(self):
        ext = os.path.splitext(self.rel_filename)[-1]
        if re.match('.pp?', ext):
            return 'fields_file'
        elif ext == '.nc':
            return 'netcdf'
        elif ext == '.png':
            return 'png'

    def set_config(self, config):
        self.config = config

    def __repr__(self):
        return '<Node {} (id={}, status={})>'\
               .format(self.name, self.id, self.status)
