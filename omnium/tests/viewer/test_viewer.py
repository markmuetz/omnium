try:
    from pyqtgraph.Qt import QtCore, QtGui
    from omnium.viewers.viewer_control import ViewerControlWindow
    test_viewer = True
except ImportError:
    test_viewer = False


if test_viewer:
    def test_viewer_launch():
        app = QtGui.QApplication([])

        viewer_control = ViewerControlWindow([], [])
        viewer_control.show()
