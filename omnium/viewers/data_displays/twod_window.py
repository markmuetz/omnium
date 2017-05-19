import numpy as np
from functools import partial
from collections import OrderedDict

from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg

from omnium.viewers.data_displays import DataDisplayWindow


class TwodWindow(DataDisplayWindow):
    name = 'Slice'

    level_slider_changed = QtCore.pyqtSignal(int)
    level_slider2_changed = QtCore.pyqtSignal(int)

    orientations = ['xy', 'xz', 'yz']
    scales = ['image', 'level', 'time', 'level/time']
    colour_maps = OrderedDict([
        ('blue-white-red', {
            'pos': np.array([0.0, 0.5, 1.0]),
            'colour': np.array([[0, 0, 255, 255],
                               [255, 255, 255, 255],
                               [255, 0, 0, 255]], dtype=np.ubyte)}),
        ('black-red-yellow-white', {
            'pos': np.array([0.0, 0.33, 0.66, 1.0]),
            'colour': np.array([[0, 0, 0, 255],
                               [255, 0, 0, 255],
                               [255, 255, 0, 255],
                               [255, 255, 255, 255]], dtype=np.ubyte)}),
        ('black-orange-red', {
            'pos': np.array([0.0, 0.5, 1.0]),
            'colour': np.array([[0, 0, 0, 255],
                               [255, 128, 0, 255],
                               [255, 0, 0, 255]], dtype=np.ubyte)}),
        ('blue-red', {
            'pos': np.array([0.0, 0.5, 1.0]),
            'colour': np.array([[0, 0, 255, 255],
                               [128, 0, 128, 255],
                               [255, 0, 0, 255]], dtype=np.ubyte)})])

    def __init__(self, parent):
        super(TwodWindow, self).__init__(parent)
        self.level_index2 = 0
        self.orientation = 'xy'
        self.scale = 'image'
        self.colour_map = 'blue-white-red'
        self._min_max_cache = {}
        self.updateColourMap(self.colour_map, False)
        self.scaleSymmetrySetting = False

    def saveState(self):
        state = super(TwodWindow, self).saveState()
        state['level_index'] = self.level_index
        state['level_index2'] = self.level_index2
        state['orientation'] = self.orientation
        state['scale'] = self.scale
        state['colour_map'] = self.colour_map
        return state

    def loadState(self, state):
        super(TwodWindow, self).loadState(state)
        self.level_index = state['level_index']
        self.level_index2 = state['level_index2']
        self.orientation = state['orientation']
        self.scale = state['scale']
        self.colour_map = state['colour_map']
        self.updateColourMap(self.colour_map, False)

        self.level_slider_changed.emit(self.level_index)
        self.level_slider2_changed.emit(self.level_index2)

    def scaleSymmetry(self):
        self.scaleSymmetrySetting = self.scaleSymmetryAction.isChecked()
        self.update()

    def updateScale(self, scale):
        self.scale = scale
        if self.scale == 'image':
            pass
        elif self.scale == 'level':
            pass
        self.update()

    def updateOrientation(self, orientation):
        self.orientation = orientation
        if self.orientation == 'xy':
            self.level_slider.setRange(0, self.cube.shape[1] - 1)
        elif self.orientation == 'xz':
            self.level_slider.setRange(0, self.cube.shape[2] - 1)
        elif self.orientation == 'yz':
            self.level_slider.setRange(0, self.cube.shape[3] - 1)
        self.update()

    def updateColourMap(self, colour_map, update=True):
        self.colour_map = colour_map
        pos, colour = map(self.colour_maps[self.colour_map].get, ('pos', 'colour'))
        cmap = pg.ColorMap(pos, colour)
        self._lut = cmap.getLookupTable(0.0, 1.0, 256)
        if update:
            self.update()

    def setupGui(self):
        super(TwodWindow, self).setupGui()

        self.menuView = QtGui.QMenu(self.menubar)
        # self.menuFile.setObjectName(_fromUtf8("menuFile"))
        self.menuView.setTitle("View")
        self.menubar.addAction(self.menuView.menuAction())

        orientationGroup = QtGui.QActionGroup(self, exclusive=True)
        for orientation in self.orientations:
            checked = orientation == self.orientation
            orientationAction = QtGui.QAction(orientation, self, checkable=True, checked=checked)
            orientationAction.triggered.connect(partial(self.updateOrientation, orientation))
            orientationGroup.addAction(orientationAction)
            self.menuView.addAction(orientationAction)

        self.menuView.addSeparator()

        scaleGroup = QtGui.QActionGroup(self, exclusive=True)
        for scale in self.scales:
            checked = scale == self.scale
            scaleAction = QtGui.QAction('Scale on {}'.format(scale),
                                        self, checkable=True, checked=checked)
            scaleAction.triggered.connect(partial(self.updateScale, scale))
            scaleGroup.addAction(scaleAction)
            self.menuView.addAction(scaleAction)

        self.scaleSymmetryAction = QtGui.QAction('Symmetric scale',
                                                 self, checkable=True, checked=checked)
        self.scaleSymmetryAction.triggered.connect(self.scaleSymmetry)
        self.menuView.addAction(self.scaleSymmetryAction)

        cmapGroup = QtGui.QActionGroup(self, exclusive=True)
        self.menuView.addSeparator()
        colourMapMenu = self.menuView.addMenu('Colour map')
        for colour_map in self.colour_maps:
            checked = colour_map == self.colour_map
            cmapAction = QtGui.QAction(colour_map, self, checkable=True, checked=checked)
            cmapAction.triggered.connect(partial(self.updateColourMap, colour_map))
            cmapGroup.addAction(cmapAction)
            colourMapMenu.addAction(cmapAction)

        self._img = pg.ImageItem(border='w')
        self._img.setOpts(axisOrder='row-major')
        glw = pg.GraphicsLayoutWidget()
        view = glw.addViewBox()
        view.addItem(self._img)

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
            if self.orientation == 'xy':
                height = self.cube.coord('level_height').points[self.level_index]
                data = self.cube[self.time_index, self.level_index].data
                self.setWindowTitle('{0}: {1:.2f}d, z: {2:.2f}m'.format(self.cube.name(),
                                                                        self.time_days,
                                                                        height))
            elif self.orientation == 'xz':
                y = self.cube.coord('grid_latitude').points[self.level_index]
                data = self.cube[self.time_index, :, self.level_index].data
                self.setWindowTitle('{0}: {1:.2f}d, y: {2:.2f}m'.format(self.cube.name(),
                                                                        self.time_days,
                                                                        y))
            elif self.orientation == 'yz':
                x = self.cube.coord('grid_longitude').points[self.level_index]
                data = self.cube[self.time_index, :, ::-1, self.level_index].data
                self.setWindowTitle('{0}: {1:.2f}d, x: {2:.2f}m'.format(self.cube.name(),
                                                                        self.time_days,
                                                                        x))
        elif self.cube.ndim == 5:
            data = self.cube[self.time_index, self.level_index, self.level_index2].data
            self.setWindowTitle('{0}: {1:.2f}d, {2:.2f}m'.format(self.cube.name(),
                                                                 self.time_days,
                                                                 height))

        kwargs = {}

        def get_key(*args):
            return ':'.join(map(str, args))

        if self.scale == 'image':
            min_max = data.min(), data.max()
        elif self.scale == 'level':
            key = get_key(self.time_index, 'all', self.orientation)
            min_max = self._get_min_max_cache(key)
            if not min_max:
                min_max = (self.cube[self.time_index].data.min(),
                           self.cube[self.time_index].data.max())
                self._min_max_cache[key] = min_max
        elif self.scale == 'time':
            key = get_key('all', self.level_index, self.orientation)
            min_max = self._get_min_max_cache(key)
            if not min_max:
                min_max = (self.cube[:, self.level_index].data.min(),
                           self.cube[:, self.level_index].data.max())
                self._min_max_cache[key] = min_max
        elif self.scale == 'level/time':
            key = get_key('all', 'all', 'all')
            min_max = self._get_min_max_cache(key)
            if not min_max:
                min_max = self.cube.data.min(), self.cube.data.max()
                self._min_max_cache[key] = min_max

        if self.scaleSymmetrySetting:
            abs_max = max(abs(min_max[0]), abs(min_max[1]))
            kwargs['levels'] = (-abs_max, abs_max)
        else:
            kwargs['levels'] = min_max

        self._img.setLookupTable(self._lut)
        self._img.setImage(data, **kwargs)

    def _get_min_max_cache(self, key):
        if key in self._min_max_cache:
            return self._min_max_cache[key]
        return None
