#!/bin/env python
"""
Proof of concept 3D UM output viewer.
Will only work with 4D (3D+time) Iris cubes.
"""
# Call with e.g. python threed_monc.py <filename> <cube_index> <size_factor> <timeout>
from logging import getLogger

logger = getLogger('omni')

from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.opengl as gl
import numpy as np
import iris

class Window(QtGui.QWidget):
    # TODO: Unify with threed_umov
    time_slider_changed = QtCore.pyqtSignal(int)
    thresh_slider_changed = QtCore.pyqtSignal(float)

    def __init__(self, filename, cube_index, size, timeout):
        super(Window, self).__init__()
        self.thresh = 0
        self.cube_index = 0
        self.filename = filename
        self.cube_index = int(cube_index)
        self.size = float(size)
        self.timeout = int(timeout)

        self.cube = iris.load(filename)[self.cube_index]

        logger.info(self.cube)

        # Create opengl widget.
        self.umov_view = gl.GLViewWidget()
        self.umov_view.opts['distance'] = 64

        # Add a grid.
        grid = gl.GLGridItem()
        grid.setSize(64, 64, 0)
        grid.setSpacing(4, 4, 0)
        self.umov_view.addItem(grid)

        # Start layout.
        self.resize(600, 400)
        self.umov_view.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        layout = QtGui.QGridLayout()
        self.setLayout(layout)
        # Sets width of 2nd column and 1st to be larger.
        layout.setColumnStretch(1, 2)
        layout.setRowStretch(0, 2)

        # Initial scatter.
        pos, size = self.get_pos_size(self.cube[self.cube_index].data)
        self.point_scatter = gl.GLScatterPlotItem(pos=pos, color=(1, 1, 1, 1), size=size)
        self.umov_view.addItem(self.point_scatter)

        # Create some controls.
        button = QtGui.QPushButton('Pause/Play')
        button.clicked.connect(self.toggle_pause_play)

        self.time_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.time_slider.setRange(0, self.cube.shape[0])
        self.time_slider.setSingleStep(1)
        self.time_slider.setPageStep(15)
        self.time_slider.setTickInterval(60)
        self.time_slider.setTickPosition(QtGui.QSlider.TicksRight)
        self.time_slider.valueChanged.connect(self.set_time_slider_value)
        self.time_slider_changed.connect(self.time_slider.setValue)

        self.thresh_slider = QtGui.QSlider(QtCore.Qt.Vertical)
        self.thresh_slider.setRange(-500, 500)
        self.thresh_slider.setSingleStep(1)
        # self.thresh_slider.setPageStep(0.01)
        self.thresh_slider.setTickInterval(100)
        self.thresh_slider.setTickPosition(QtGui.QSlider.TicksRight)
        self.thresh_slider.valueChanged.connect(self.set_thresh_slider_value)
        self.thresh_slider_changed.connect(self.thresh_slider.setValue)
        self.thresh_slider.setValue(self.thresh * 100)

        # Populate layout.
        layout.addWidget(button, 4, 0)
        layout.addWidget(self.umov_view, 0, 1, 3, 1)  # spans 3 rows.
        layout.addWidget(self.time_slider, 4, 1)
        layout.addWidget(self.thresh_slider, 0, 0, 3, 1)

        # Setup animation callback.
        self.timer = QtCore.QTimer(self)
        self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.update)
        self.paused = False
        self.play()

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
        self.render()

    def set_thresh_slider_value(self, value):
        self.thresh = value / 100.
        self.render()

    def update(self):
        self.cube_index += 1
        self.cube_index %= self.cube.shape[0]

        self.time_slider_changed.emit(self.cube_index)

    def render(self):
        pos, size = self.get_pos_size(self.cube[self.cube_index].data)

        self.umov_view.removeItem(self.point_scatter)
        self.point_scatter = gl.GLScatterPlotItem(pos=pos, color=(1, 1, 1, 0.5), size=size)
        self.umov_view.addItem(self.point_scatter)

    def get_pos_size(self, data):
        # Apply comparison.
        d = (data > self.thresh)
        # Get value of array where comparison is True.
        size = data[d] * self.size
        # order is x, y, z
        pos_indices = np.array(np.where(d)).T

        # Map indices to values.
        pos = np.empty_like(pos_indices, dtype=np.float64)
        xy_map = np.linspace(-30, 30, 16)
        z_map = np.linspace(0, 40, 101)

        pos[:, 0] = xy_map[pos_indices[:, 0]]
        pos[:, 1] = xy_map[pos_indices[:, 1]]
        pos[:, 2] = z_map[pos_indices[:, 2]]

        return pos, size


