import sys

ARGS = [(['filenames'], {'nargs': '+'})]

def main(args):
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        from pyqtgraph.Qt import QtCore, QtGui
        from omnium.experimental.omnium_viewer import MainWindow

        app = QtGui.QApplication(sys.argv)

        filenames = args.filenames
        window = MainWindow(filenames)
        window.show()
        sys.exit(app.exec_())
