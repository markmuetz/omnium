import numpy as np

from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg

class TwodWindow(QtGui.QMainWindow):
    def __init__(self):
        super(TwodWindow, self).__init__()
        self._img = pg.ImageItem(border='w')
        self._img.setOpts(axisOrder='row-major')
        glw = pg.GraphicsLayoutWidget()
        view = glw.addViewBox()
        view.addItem(self._img)
        self.setCentralWidget(glw)
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

    def setData(self, data, ):
        self._img.setImage(data)



