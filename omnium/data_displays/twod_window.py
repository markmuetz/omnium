import numpy as np

from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg

class TwodWindow(QtGui.QMainWindow):
    level_slider_changed = QtCore.pyqtSignal(int)

    def __init__(self, parent):
        super(TwodWindow, self).__init__(parent)
        self.time_index = 0
        self.level_index = 0
        self.setupGui()

    def setupGui(self):
        self._img = pg.ImageItem(border='w')
        self._img.setOpts(axisOrder='row-major')
        glw = pg.GraphicsLayoutWidget()
        view = glw.addViewBox()
        view.addItem(self._img)
        lut = np.zeros((256,3), dtype=np.ubyte)

	pos = np.array([0.0, 
                        0.5, 
			1.0])
	color = np.array([[255,255,255,255], 
                          [255,128,0,255], 
                          [255,255,0,255]], dtype=np.ubyte)
	cmap = pg.ColorMap(pos, color)
	lut = cmap.getLookupTable(0.0, 1.0, 256)
        self._img.setLookupTable(lut)
        self._closed_callback = None

        self.level_slider = QtGui.QSlider(QtCore.Qt.Vertical)
        self.level_slider_changed.connect(self.level_slider.setValue)
        self.level_slider.valueChanged.connect(self.set_level_slider_value)

        lhs_hsplitter = QtGui.QSplitter()
        lhs_hsplitter.addWidget(glw)
        lhs_hsplitter.addWidget(self.level_slider)

        central_widget = QtGui.QWidget()
        main_layout = QtGui.QHBoxLayout()
        main_layout.addWidget(lhs_hsplitter)
        central_widget.setLayout(main_layout)

        self.setCentralWidget(central_widget)

    def set_level_slider_value(self, value):
        self.level_index = value
        self.update()

    def setData(self, cube):
        self.cube = cube
        self.level_slider.setRange(0, self.cube.shape[1] - 1)
        self.update()

    def update(self):
        data = self.cube[self.time_index, self.level_index].data
        self._img.setImage(data)
