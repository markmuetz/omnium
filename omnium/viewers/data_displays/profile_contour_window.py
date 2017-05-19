import numpy as np

from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg

from omnium.viewers.data_displays import DataDisplayWindow


class ProfileContourWindow(DataDisplayWindow):
    name = 'Slice'

    def setupGui(self):
        super(ProfileContourWindow, self).setupGui()

        glw = pg.GraphicsLayoutWidget()
        self.view = glw.addViewBox()

        self.view.setAspectLocked()

        self.lhs_hsplitter = QtGui.QSplitter()
        self.lhs_hsplitter.addWidget(glw)

        self.main_layout.addWidget(self.lhs_hsplitter)

    def setCube(self, cube):
        assert cube.ndim == 4
        self.cube = cube

        data = self.cube.data.mean(axis=(2, 3))

        img = pg.ImageItem(data)
        self.view.addItem(img)

        # generate empty curves
        curves = []
        levels = np.linspace(data.min(), data.max(), 10)
        for i in range(len(levels)):
            v = levels[i]
            # generate isocurve with automatic color selection
            c = pg.IsocurveItem(level=v, pen=(i, len(levels)*1.5))
            c.setParentItem(img)  # make sure isocurve is always correctly displayed over image
            c.setZValue(10)
            curves.append(c)

        self.update()

    def update(self):
        pass
