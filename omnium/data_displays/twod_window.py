import numpy as np

from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg

from omnium.data_displays import DataDisplayWindow

class TwodWindow(DataDisplayWindow):
    level_slider_changed = QtCore.pyqtSignal(int)
    level_slider2_changed = QtCore.pyqtSignal(int)

    def setupGui(self):
        super(TwodWindow, self).setupGui()

        self.colour_map = 'black-orange-red'

        self._img = pg.ImageItem(border='w')
        self._img.setOpts(axisOrder='row-major')
        glw = pg.GraphicsLayoutWidget()
        view = glw.addViewBox()
        view.addItem(self._img)
        lut = np.zeros((256,3), dtype=np.ubyte)

        if self.colour_map == 'black-orange-red':
            pos = np.array([0.0, 0.5, 1.0])
            colour = np.array([[0, 0, 0, 255], 
                               [255, 128, 0, 255], 
                               [255, 0, 0, 255]], dtype=np.ubyte)
        else:
            pos = np.array([0.0, 0.5, 1.0])
            colour = np.array([[0, 0, 255, 255], 
                               [128, 0, 128, 255], 
                               [255, 0, 0, 255]], dtype=np.ubyte)
	cmap = pg.ColorMap(pos, colour)
	lut = cmap.getLookupTable(0.0, 1.0, 256)
        self._img.setLookupTable(lut)
        self._closed_callback = None

        self.lhs_hsplitter = QtGui.QSplitter()
        self.lhs_hsplitter.addWidget(glw)

        self.main_layout.addWidget(self.lhs_hsplitter)

    def setLevelSliderValue(self, value):
        self.level_index = value
        self.update()

    def setLevelSlider2Value(self, value):
        self.level_index2 = value
        self.update()

    def setCube(self, cube):
        assert 3 <= cube.ndim <= 5
        self.cube = cube
        if self.cube.ndim >= 4:
            self.level_slider = QtGui.QSlider(QtCore.Qt.Vertical)
            self.level_slider_changed.connect(self.level_slider.setValue)
            self.level_slider.valueChanged.connect(self.setLevelSliderValue)
            self.level_slider.setRange(0, self.cube.shape[1] - 1)
            self.lhs_hsplitter.addWidget(self.level_slider)

        if self.cube.ndim == 5:
            self.level_slider2 = QtGui.QSlider(QtCore.Qt.Vertical)
            self.level_slider2_changed.connect(self.level_slider2.setValue)
            self.level_slider2.valueChanged.connect(self.setLevelSlider2Value)
            self.level_slider2.setRange(0, self.cube.shape[2] - 1)
            self.lhs_hsplitter.addWidget(self.level_slider2)

        self.update()

    def update(self):
        if self.cube.ndim == 3:
            data = self.cube[self.time_index].data
            self.setWindowTitle('{0}: {1:.2f}d'.format(self.cube.name(), self.time_days))
        elif self.cube.ndim == 4:
            height = self.cube.coord('level_height').points[self.level_index]
            data = self.cube[self.time_index, self.level_index].data
            self.setWindowTitle('{0}: {1:.2f}d, {2:.2f}m'.format(self.cube.name(), 
                                                                 self.time_days,
                                                                 height))
        elif self.cube.ndim == 5:
            data = self.cube[self.time_index, self.level_index, self.level_index2].data
            self.setWindowTitle('{0}: {1:.2f}d, {2:.2f}m'.format(self.cube.name(), 
                                                                 self.time_days,
                                                                 height))
        self._img.setImage(data)
