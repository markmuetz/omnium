import numpy as np

from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg

class PlotWindow(QtGui.QMainWindow):
    level_slider_changed = QtCore.pyqtSignal(int)

    def __init__(self, parent):
        super(PlotWindow, self).__init__(parent)
        self.time_index = 0
        self.level_index = 0
        self.setupGui()

    def setupGui(self):
        self.plotWidget = pg.PlotWidget(self)

        lhs_hsplitter = QtGui.QSplitter()
        lhs_hsplitter.addWidget(self.plotWidget)

        central_widget = QtGui.QWidget()
        main_layout = QtGui.QHBoxLayout()
        main_layout.addWidget(lhs_hsplitter)
        central_widget.setLayout(main_layout)

        self.setCentralWidget(central_widget)

    def setData(self, cubes):
        for cube in cubes:
            self.plotWidget.plot(range(cube.shape[0]), cube.data.mean(axis=(1, 2, 3)))
        self.time_line = pg.InfiniteLine(movable=False, angle=90, label='t={value:0.2f}', 
                                         labelOpts={'position':0.1, 'color': (200,200,100), 'fill': (200,200,200,50), 'movable': True})
        self.plotWidget.addItem(self.time_line)
        self.update()

    def update(self):
        self.time_line.setPos(self.time_index)

