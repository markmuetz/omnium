"""Launch MONC 3D cube viewer"""
# PyLint has difficulty loading the Qt classes correctly:
# pylint: disable=no-member
import os
import sys
import importlib
from glob import glob
from logging import getLogger

from omnium.node_dag import NodeDAG

logger = getLogger('omni')

ARGS = [(['--group', '-g'], {}),
        (['--timeout', '-t'], {'default': 50, 'type': float}),
        (['--data-source', '-d'], {'default': 'UM', 'choices': ['UM', 'MONC']})]


def main(args, config, process_classes):
    try:
        # TODO: how do you do this?
        # QtCore = importlib.import_module('pyqtgraph.Qt', 'QtCore')
        # QtGui = importlib.import_module('pyqtgraph.Qt', 'QtGui')
        from pyqtgraph.Qt import QtCore, QtGui
    except ImportError:
        logger.error('Qt not installed on this computer')
        return 1

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        # TODO: and this?
        # Window = importlib.import_module('omnium', 'threed_monc.Window')
        from omnium.threed import Window

        # logger.info('Starting app')
        app = QtGui.QApplication(sys.argv)

        dag = NodeDAG(config, process_classes)
        group = dag.get_group(args.group)
        filenames = [n.filename(config) for n in group.nodes]

        logger.debug(args)
        window = Window(filenames, args.data_source, args.timeout)
        window.show()
        sys.exit(app.exec_())
