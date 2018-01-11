from pyqtgraph.Qt import QtCore, QtGui
from omnium.viewers.viewer_control import ViewerControlWindow

def test_viewer_launch():

    app = QtGui.QApplication([])

    viewer_control = ViewerControlWindow([], [])
    viewer_control.show()
