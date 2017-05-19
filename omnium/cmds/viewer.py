import sys

ARGS = [(['filenames'], {'nargs': '*'}),
        (['--state', '-s'], {'nargs': '?', 'default': None}),
        (['--ignore-prev-settings'], {'action': 'store_true', 'default': False})]


def main(args):
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        from pyqtgraph.Qt import QtCore, QtGui
        from omnium.viewers.viewer_control import ViewerControlWindow

        app = QtGui.QApplication(sys.argv)

        viewer_control = ViewerControlWindow(args.state, args.filenames)
        viewer_control.show()
        sys.exit(app.exec_())
