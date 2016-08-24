from sqlalchemy import Integer, ForeignKey, String, Column, Table, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

node_to_node = Table("node_to_node", Base.metadata,
    Column("from_node_id", Integer, ForeignKey("nodes.id"), primary_key=True),
    Column("to_node_id", Integer, ForeignKey("nodes.id"), primary_key=True)
)

statuses = Enum('missing', 'processing', 'done', name='statuses')

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
    
    batch_id = Column(Integer, ForeignKey('batches.id'))
    nodes = relationship('Node', backref='group')

    def __repr__(self):
        return '<Group {} (id={}, status={})>'\
               .format(self.name, self.id, self.status)

class Node(Base):
    __tablename__ = 'nodes'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    filename = Column(String)
    process = Column(String)
    status = Column(statuses)
    section = Column(Integer)
    item = Column(Integer)

    group_id = Column(Integer, ForeignKey('groups.id'))
    to_nodes = relationship("Node",
                            secondary=node_to_node,
                            primaryjoin=id==node_to_node.c.from_node_id,
                            secondaryjoin=id==node_to_node.c.to_node_id,
                            backref="from_nodes"
    )

    def _filename(self, config):
        return self.filename_tpl.format(config.settings.work_dir)

    def __repr__(self):
        return '<Node {} (id={}, status={})>'\
               .format(self.name, self.id, self.status)

