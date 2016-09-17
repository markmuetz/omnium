"""
Proof of concept 3D UM output viewer.
Will only work with 4D (3D+time) Iris cubes.
"""
# Call with e.g. python threed_monc.py <filename> <cube_index> <size_factor> <timeout>
# PyLint has difficulty loading the Qt classes correctly:
# pylint: disable=no-member
import re
from logging import getLogger

from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.opengl as gl
import numpy as np
import iris

from stash import Stash

logger = getLogger('omni')


class Window(QtGui.QWidget):
    time_slider_changed = QtCore.pyqtSignal(int)
    thresh_slider_changed = QtCore.pyqtSignal(float)
    thresh_slider_changed2 = QtCore.pyqtSignal(float)

    def __init__(self, filenames, data_source, timeout):
        super(Window, self).__init__()
        self.data_source = data_source
        self.timeout = int(timeout)

        self.thresh = 0
        self.thresh2 = 0

        self.cubes = []
        for filename in filenames:
            cubes = iris.load(filename)
            for cube in cubes:
                self.cubes.append(cube)

        stash = Stash()
        stash.rename_unknown_cubes(self.cubes, True)
        self.cb = QtGui.QComboBox()
        self.cb2 = QtGui.QComboBox()
        for index, cube in enumerate(self.cubes):
            name = re.sub(' +', ' ', cube.name())
            self.cb.addItem(name)
            self.cb2.addItem(name)
            print((index, cube.name()))

        self.cube_index = 0
        self.cube_index2 = 0
        self.cb.currentIndexChanged.connect(self.cb_changed)
        self.cb2.currentIndexChanged.connect(self.cb2_changed)
        self.cube = self.cubes[0]
        self.cube2 = self.cubes[0]

        self.set_min_max()
        self.set_min_max2()
        logger.info(self.cube)

        # Create opengl widget.
        self.view = gl.GLViewWidget()
        self.view.opts['distance'] = 64

        # Add a grid.
        grid = gl.GLGridItem()
        grid.setSize(64, 64, 0)
        grid.setSpacing(4, 4, 0)
        self.view.addItem(grid)

        # Start layout.
        self.resize(600, 400)
        self.view.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        layout = QtGui.QGridLayout()
        self.setLayout(layout)
        # Sets width of 2nd column and 1st to be larger.
        layout.setColumnStretch(1, 2)
        layout.setRowStretch(0, 3)

        # Initial scatter.
        pos, size = self.get_pos_size(self.cube[self.cube_index].data, 0)
        self.point_scatter = gl.GLScatterPlotItem(pos=pos, color=(1, 1, 1, 1), size=size)
        self.view.addItem(self.point_scatter)

        pos2, size2 = self.get_pos_size(self.cube2[self.cube_index2].data, 1)
        self.point_scatter2 = gl.GLScatterPlotItem(pos=pos2, color=(0, 1, 1, 1), size=size2)
        self.view.addItem(self.point_scatter2)

        # Create some controls.
        button = QtGui.QPushButton('Pause/Play')
        button.clicked.connect(self.toggle_pause_play)

        self.time_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.time_slider.setRange(0, self.cube.shape[0] - 1)
        self.time_slider.setSingleStep(1)
        self.time_slider.setPageStep(15)
        self.time_slider.setTickInterval(60)
        self.time_slider.setTickPosition(QtGui.QSlider.TicksRight)
        self.time_slider.valueChanged.connect(self.set_time_slider_value)
        self.time_slider_changed.connect(self.time_slider.setValue)

        self.thresh_slider = QtGui.QSlider(QtCore.Qt.Vertical)
        self.thresh_slider.setRange(0, 100)
        self.thresh_slider.setSingleStep(1)
        # self.thresh_slider.setPageStep(0.01)
        self.thresh_slider.setTickInterval(100)
        self.thresh_slider.setTickPosition(QtGui.QSlider.TicksRight)
        self.thresh_slider.valueChanged.connect(self.set_thresh_slider_value)
        self.thresh_slider_changed.connect(self.thresh_slider.setValue)
        self.thresh_slider.setValue(self.thresh * 100)

        self.thresh_slider2 = QtGui.QSlider(QtCore.Qt.Vertical)
        self.thresh_slider2.setRange(0, 100)
        self.thresh_slider2.setSingleStep(1)
        # self.thresh_slider2.setPageStep(0.01)
        self.thresh_slider2.setTickInterval(100)
        self.thresh_slider2.setTickPosition(QtGui.QSlider.TicksRight)
        self.thresh_slider2.valueChanged.connect(self.set_thresh_slider_value2)
        self.thresh_slider_changed2.connect(self.thresh_slider2.setValue)
        self.thresh_slider2.setValue(self.thresh * 100)

        # Populate layout.
        layout.addWidget(button, 6, 0, 1, 2)
        layout.addWidget(self.view, 0, 2, 3, 1)  # spans 3 rows.
        layout.addWidget(self.time_slider, 4, 2)
        layout.addWidget(self.thresh_slider, 0, 0, 3, 1)
        layout.addWidget(self.thresh_slider2, 0, 1, 3, 1)
        layout.addWidget(self.cb, 4, 0, 1, 2)
        layout.addWidget(self.cb2, 5, 0, 1, 2)

        # Setup animation callback.
        self.timer = QtCore.QTimer(self)
        self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.update)
        self.paused = False
        self.play()

    def cb_changed(self, i):
        cube = self.cubes[i]
        if len(cube.shape) == 4:
            self.cube = cube
        print(self.cube.name())
        self.set_min_max()
        self.set_min_max2()
        self.render()

    def cb2_changed(self, i):
        cube = self.cubes[i]
        if len(cube.shape) == 4:
            self.cube2 = cube
        print(self.cube2.name())
        self.set_min_max()
        self.set_min_max2()
        self.render()

    def set_min_max(self):
        self.min_val = self.cube.data.min()
        self.max_val = self.cube.data.max()
        self.size = 30 / self.max_val

    def set_min_max2(self):
        self.min_val2 = self.cube2.data.min()
        self.max_val2 = self.cube2.data.max()
        self.size2 = 30 / self.max_val2

    def toggle_pause_play(self):
        self.paused = not self.paused
        if self.paused:
            self.pause()
        else:
            self.play()

    def play(self):
        self.timer.start(self.timeout)

    def pause(self):
        self.timer.stop()

    def set_time_slider_value(self, value):
        self.cube_index = value
        self.cube_index2 = value
        self.render()

    def set_thresh_slider_value(self, value):
        frac = value / 100.
        self.thresh = self.min_val + (self.max_val - self.min_val) * frac
        self.render()

    def set_thresh_slider_value2(self, value):
        frac = value / 100.
        self.thresh2 = self.min_val2 + (self.max_val2 - self.min_val2) * frac
        self.render()

    def update(self):
        self.cube_index += 1
        self.cube_index %= self.cube.shape[0]

        self.cube_index2 += 1
        self.cube_index2 %= self.cube.shape[0]

        self.time_slider_changed.emit(self.cube_index)

    def render(self):
        pos, size = self.get_pos_size(self.cube[self.cube_index].data, 0)
        pos2, size2 = self.get_pos_size(self.cube2[self.cube_index2].data, 1)

        self.view.removeItem(self.point_scatter)
        self.point_scatter = gl.GLScatterPlotItem(pos=pos, color=(1, 1, 1, 1), size=size)
        self.view.addItem(self.point_scatter)

        self.view.removeItem(self.point_scatter2)
        self.point_scatter2 = gl.GLScatterPlotItem(pos=pos2, color=(0, 1, 1, 1), size=size2)
        self.view.addItem(self.point_scatter2)

    def get_pos_size(self, data, index):
        # Apply comparison.
        if index == 0:
            d = (data > self.thresh)
            # Get value of array where comparison is True.
            size = data[d] * self.size
        elif index == 1:
            d = (data > self.thresh2)
            # Get value of array where comparison is True.
            size = data[d] * self.size2

        if self.data_source == 'UM':
            # Needs some unpacking:
            # np.where(d) gets indices where comparison is true, but needs transposed.
            # indices are currently in order z, x, y, np.roll fixes this.
            pos_indices = np.roll(np.array(np.where(d)).T, -1, axis=1)

            # Map indices to values.
            pos = np.empty_like(pos_indices, dtype=np.float64)
            pos[:, 0] = self.cube.coord('grid_longitude')\
                            .points[pos_indices[:, 0]] / 1000
            pos[:, 1] = self.cube.coord('grid_latitude')\
                            .points[pos_indices[:, 1]] / 1000
            pos[:, 2] = self.cube.coord('level_height')\
                            .points[pos_indices[:, 2]] / 1000

            pos -= [32, 32, 0]
        elif self.data_source == 'MONC':
            # order is x, y, z
            pos_indices = np.array(np.where(d)).T

            # Map indices to values.
            pos = np.empty_like(pos_indices, dtype=np.float64)
            # TODO: x and y must have same dims currently.
            xy_map = np.linspace(-30, 30, data.shape[0])
            z_map = np.linspace(0, 40, data.shape[-1])

            pos[:, 0] = xy_map[pos_indices[:, 0]]
            pos[:, 1] = xy_map[pos_indices[:, 1]]
            pos[:, 2] = z_map[pos_indices[:, 2]]

        return pos, size
