import datetime as dt

from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg


class DataDisplayWindow(QtGui.QMainWindow):
    title = '##Data Display##'
    accepts_multiple_cubes = False

    def __init__(self, parent):
        super(DataDisplayWindow, self).__init__(parent)
        self.time_index = 0
        self.level_index = 0
        self.time_days = 0.

    def loadState(self, state):
        self.move(state['pos'])
        self.resize(state['size'])

    def saveState(self):
        state = {'name': self.name}
        state['pos'] = self.pos()
        state['size'] = self.size()
        return state

    def setTime(self, time):
        time_hrs_since_1970 = time
        delta_1970_2000 = dt.datetime(2000, 1, 1) - dt.datetime(1970, 1, 1)
        self.time_days = (dt.timedelta(hours=time_hrs_since_1970) -
                          delta_1970_2000).total_seconds() / 86400.

        for i, test_time in enumerate(self.cube.coord('time').points):
            if test_time == time:
                self.time_index = i
                return
            elif test_time > time:
                if i > 0:
                    self.time_index = i - 1
                else:
                    self.time_index = 0
                return
        self.time_index = self.cube.shape[0] - 1

    def debug(self):
        import ipdb
        ipdb.set_trace()

    def setupGui(self):
        self.menubar = QtGui.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(20, 20, 800, 23))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtGui.QMenu(self.menubar)
        # self.menuFile.setObjectName(_fromUtf8("menuFile"))
        self.menuFile.setTitle("File")
        self.menubar.addAction(self.menuFile.menuAction())
        self.setMenuBar(self.menubar)

        debugAction = QtGui.QAction('&Debug', self)
        debugAction.setShortcut('Ctrl+D')
        debugAction.triggered.connect(self.debug)

        self.menuFile.addAction(debugAction)

        self.setWindowTitle(self.title)
        central_widget = QtGui.QWidget()
        self.main_layout = QtGui.QHBoxLayout()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)
