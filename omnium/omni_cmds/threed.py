"""Launch MONC 3D cube viewer"""
# PyLint has difficulty loading the Qt classes correctly:
# pylint: disable=no-member
import os
import sys
import importlib
from glob import glob
from logging import getLogger

logger = getLogger('omni')

ARGS = [(['--cube-index', '-c'], {'default': 0, 'type': int}),
        (['--size', '-s'], {'default': 0.5, 'type': float}),
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

        # TODO: Picking first is arbitrary!
        group = config['groups'].keys()[0]
        filename_glob = config['groups'][group]['filename_glob']
        work_dir = os.path.expandvars(config['computers'][config['computer_name']]['dirs']['work'])
        glob_full = os.path.join(work_dir, filename_glob)
        logger.debug(glob_full)
        filename = glob(glob_full)[0]

        logger.debug(args)
        window = Window(filename, args.data_source, args.cube_index,
                        args.size, args.timeout)
        window.show()
        sys.exit(app.exec_())
