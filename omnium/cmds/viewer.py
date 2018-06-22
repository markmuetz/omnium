"""Launch omnium viewer for looking at UM output files"""
import sys

ARGS = [(['filenames'], {'nargs': '*'}),
        (['--state', '-s'], {'nargs': '?', 'default': None}),
        (['--ignore-prev-settings'], {'action': 'store_true', 'default': False})]
RUN_OUTSIDE_SUITE = True


def main(suite, args):
    from pyqtgraph.Qt import QtCore, QtGui
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        from omnium.viewers.viewer_control import ViewerControlWindow

        app = QtGui.QApplication(sys.argv)

        viewer_control = ViewerControlWindow(args.state, args.filenames)
        viewer_control.show()
        return app.exec_()
