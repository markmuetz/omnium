import sys

ARGS = [(['filenames'], {'nargs': '+'}),
        (['--data-source', '-d'], {'default': 'UM', 'choices': ['UM', 'MONC']})]


def main(args):
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        from pyqtgraph.Qt import QtCore, QtGui
        from omnium.threed_viewer import MainWindow

        app = QtGui.QApplication(sys.argv)

        filenames = args.filenames
        window = MainWindow(filenames, args.data_source)
        window.show()
        sys.exit(app.exec_())
