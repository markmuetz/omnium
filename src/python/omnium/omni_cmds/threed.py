"""Launch 3D cube viewer"""
# PyLint has difficulty loading the Qt classes correctly:
# pylint: disable=no-member
import sys
from logging import getLogger

logger = getLogger('omni')

ARGS = []


def main(args, config, process_classes):
    try:
        from pyqtgraph.Qt import QtCore, QtGui
    except ImportError:
        logger.error('Qt not installed on this computer')
        return 1

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        from omnium.threed_umov import Window

        logger.info('Starting app')
        app = QtGui.QApplication(sys.argv)
        window = Window(config)
        window.show()
        sys.exit(app.exec_())
