"""
Proof of concept 3D UM output viewer.
Will only work with 4D (3D+time) Iris cubes.
"""
import os
import re
import cPickle
from logging import getLogger

from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.opengl as gl
import numpy as np
import iris

from omnium.stash import Stash

logger = getLogger('omni')


class MainWindow(QtGui.QMainWindow):
    thresh_slider_changed = QtCore.pyqtSignal(float)
    size_slider_changed = QtCore.pyqtSignal(float)
    time_slider_changed = QtCore.pyqtSignal(int)
    colours = [(1, 1, 1, 1),
               (0, 1, 1, 1),
               (0, 0, 1, 1),
               (1, 0, 1, 1),
               (1, 0.5, 1, 1),
               (1, 0, 0, 1),
               (1, 0.5, 0, 1),
               (1, 1, 0, 1)]

    def __init__(self, filenames, data_source='UM', timeout=250):
        super(MainWindow, self).__init__()
        self.filenames = filenames
        self.data_source = data_source
        self.stash = Stash()
        self.timeout = timeout
        self.rendered_point_scatters = {}
        self.point_scatters = {}
        self.cube_settings = {}
        self.time_index = 0
        self.cube_index = None
        self.cubes = []
        self.zn = None
        self.thresh = 0.

        self.setupGui()
        self.addVarItems()
        self.time_slider.setRange(0, self.cubes[0].shape[0])
        self.time_slider.setSingleStep(1)
        self.time_slider.setPageStep(15)
        self.time_slider.setTickInterval(60)
        self.time_slider.setTickPosition(QtGui.QSlider.TicksRight)
        self.time_slider.valueChanged.connect(self.set_time_slider_value)
        self.time_slider_changed.connect(self.time_slider.setValue)

        self.timer = QtCore.QTimer(self)
        self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.fwd)

    def back(self):
        self.time_slider_changed.emit(self.time_index - 1)

    def pause(self):
        self.timer.stop()

    def play(self):
        timeout = int(self.ui_timeout.text())
        self.timer.start(timeout)

    def fwd(self):
        self.time_slider_changed.emit(self.time_index + 1)

    def go(self):
        self.time_slider_changed.emit(int(self.ui_time_index.text()))

    def pick_colour(self):
        if self.cube_index is not None:
            colour = QtGui.QColorDialog.getColor().getRgbF()
            self.cube_settings[self.cube_index]['colour'] = colour

            self.point_scatters.pop(self.cube_index)
            self.add_remove()
            self.add_cube(self.cube_index)
            self.add_remove()


    def set_time_slider_value(self, value):
        self.time_index = value
	if self.time_index == self.cubes[0].shape[0]:
	    if self.ui_loop.isChecked():
		self.time_index = 0
	    else:
		return
	
        self.ui_time_index.setText(str(self.time_index))
        old_point_scatters_keys = self.point_scatters.keys()
        self.point_scatters = {}
        self.add_remove()
        for cube_index in old_point_scatters_keys:
            self.add_cube(cube_index)
        self.add_remove()

    def set_thresh_slider_value(self, value):
        frac = (100 - value) / 100.
        if self.cube_index is not None and self.cube_index in self.rendered_point_scatters:
            cube = self.cubes[self.cube_index]
            thresh = cube.data.min() + (cube.data.max() - cube.data.min()) * frac
            self.cube_settings[self.cube_index]['thresh'] = thresh

            self.point_scatters.pop(self.cube_index)
            self.add_remove()
            self.add_cube(self.cube_index)
            self.add_remove()
	    self.ui_thresh.setText('{0:.3f}'.format(thresh))

    def set_size_slider_value(self, value):
        if self.cube_index is not None and self.cube_index in self.rendered_point_scatters:
            cube = self.cubes[self.cube_index]
            self.cube_settings[self.cube_index]['size_scale'] = value

            self.point_scatters.pop(self.cube_index)
            self.add_remove()
            self.add_cube(self.cube_index)
            self.add_remove()
	    self.ui_size.setText('{0:.3f}'.format(value))

    def addCube(self, parent, cube):
        cube_name = ' '.join(cube.name().split())
        cube_item = QtGui.QTreeWidgetItem(parent, [cube_name])
        cube_item.setData(0, QtCore.Qt.UserRole, len(self.cubes))
        cube_item.setCheckState(0, QtCore.Qt.Unchecked)
	if self.data_source == 'MONC' and self.zn == None:
	    try:
		self.zn = cube.coord('zn').points
	    except iris.exceptions.CoordinateNotFoundError:
		pass
        self.cubes.append(cube)

    def addFile(self, root, filename):
        fn = os.path.basename(filename)
        file_item = QtGui.QTreeWidgetItem(root, [fn])
        file_item.setChildIndicatorPolicy(QtGui.QTreeWidgetItem.ShowIndicator)
        file_item.setData(0, QtCore.Qt.UserRole, fn)
        file_item.setExpanded(True)
        cubes = iris.load(filename)

        if self.data_source == 'UM':
            self.stash.rename_unknown_cubes(cubes, True)
        
        for i, cube in enumerate(cubes):
            self.addCube(file_item, cube)

    def addVarItems(self):
        root = self.var_selector.invisibleRootItem()
        for filename in self.filenames:
            self.addFile(root, filename)


    def get_pos_size(self, cube, thresh, size_scale, cube_max):
        print(cube.shape)
        d = (cube.data > thresh)
        multiplier = size_scale / cube_max

        # Get value of array where comparison is True.
        size = cube.data[d] * multiplier
        # size = 5
        # Needs some unpacking:
        # np.where(d) gets indices where comparison is true, but needs transposed.
        # indices are currently in order z, x, y, np.roll fixes this.
        if self.data_source == 'UM':
            # Needs some unpacking:
            # np.where(d) gets indices where comparison is true, but needs transposed.
            # indices are currently in order z, x, y, np.roll fixes this.
            pos_indices = np.roll(np.array(np.where(d)).T, -1, axis=1)

            # Map indices to values.
            pos = np.empty_like(pos_indices, dtype=np.float64)
            pos[:, 0] = cube.coord('grid_longitude')\
                        .points[pos_indices[:, 0]] / 1000
            pos[:, 1] = cube.coord('grid_latitude')\
                        .points[pos_indices[:, 1]] / 1000
            pos[:, 2] = cube.coord('level_height')\
                        .points[pos_indices[:, 2]] / 1000

            pos -= [32, 32, 0]
        elif self.data_source == 'MONC':
            # order is x, y, z
            pos_indices = np.array(np.where(d)).T

            # Map indices to values.
            pos = np.empty_like(pos_indices, dtype=np.float64)
            # TODO: x and y must have same dims currently.
            # TODO: these need to be calculated properly.
            xy_map = np.linspace(-(48 - 0.75), 48 - 0.75, cube.shape[0])
            # z_map = np.linspace(0, 40, cube.shape[-1])
	    z_map = self.zn / 1000

            pos[:, 0] = xy_map[pos_indices[:, 0]]
            pos[:, 1] = xy_map[pos_indices[:, 1]]
            pos[:, 2] = z_map[pos_indices[:, 2]]

        return pos, size

    def add_remove(self):
        for index in self.point_scatters.keys():
            if index not in self.rendered_point_scatters:
                point_scatter = self.point_scatters[index]
                self.view.addItem(point_scatter)
                self.rendered_point_scatters[index] = point_scatter

        for index in self.rendered_point_scatters.keys():
            if index not in self.point_scatters:
                point_scatter = self.rendered_point_scatters.pop(index)
                self.view.removeItem(point_scatter)


    def add_cube(self, cube_index):
        cube = self.cubes[cube_index]
        thresh = self.cube_settings[cube_index]['thresh']
        colour = self.cube_settings[cube_index]['colour']
        size_scale = self.cube_settings[cube_index]['size_scale']
        cube_max = self.cube_settings[cube_index]['cube_max']

        pos, size = self.get_pos_size(cube[self.time_index], thresh, size_scale, cube_max)
        point_scatter = gl.GLScatterPlotItem(pos=pos, color=colour, size=size)
        self.point_scatters[cube_index] = point_scatter

    def handleVarSelectorChanged(self, item, column):
        data = item.data(column, QtCore.Qt.UserRole)
        if item.checkState(column) == QtCore.Qt.Checked:
            index = data.toPyObject()
            cube = self.cubes[index]
            print(cube.name())
            print('checked')

            if index not in self.cube_settings:
                self.cube_settings[index] = {}
                colour = self.colours[index % len(self.colours)]
                self.cube_settings[index]['colour'] = colour
                self.cube_settings[index]['thresh'] = cube.data.min()
                self.cube_settings[index]['size_scale'] = 5
                self.cube_settings[index]['cube_max'] = cube.data.max()
            # Initial scatter.
            self.add_cube(index)
            self.add_remove()

        elif item.checkState(column) == QtCore.Qt.Unchecked:
            index = data.toPyObject()
            if index in self.point_scatters:
                self.point_scatters.pop(index)
                self.add_remove()


    def selectedItemChanged(self):
        item = self.var_selector.selectedItems()[0]
        data = item.data(0, QtCore.Qt.UserRole)
        index = data.toPyObject()
        self.cube_index = index
        cube = self.cubes[index]
        print(cube.name())
        self.var_info.setText(cube.__str__())
        if 'thresh' in self.cube_settings[index]:
            thresh = self.cube_settings[index]['thresh']
            frac = (thresh - cube.data.min()) / (cube.data.max() - cube.data.min())
            value = 100 - 100 * frac 
            self.thresh_slider_changed.emit(value)
        if 'size_scale' in self.cube_settings[index]:
            size_scale = self.cube_settings[index]['size_scale']
            self.size_slider_changed.emit(size_scale)


    def loadSettings(self):
        try:
            self.cube_settings = cPickle.load(open('settings.pkl', 'r'))
        except:
            print('Could not load settings')

    def saveSettings(self):
        cPickle.dump(self.cube_settings, open('settings.pkl', 'w'))

    def setupGui(self):
        self.resize(800, 600)
        central_widget = QtGui.QWidget()

        self.menubar = QtGui.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(20, 20, 800, 23))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtGui.QMenu(self.menubar)
        # self.menuFile.setObjectName(_fromUtf8("menuFile"))
        self.menuFile.setTitle("File")
        self.menubar.addAction(self.menuFile.menuAction())
        self.setMenuBar(self.menubar)

        loadSettingsAction = QtGui.QAction('&Load Settings', self)        
        loadSettingsAction.setShortcut('Ctrl+L')
        loadSettingsAction.setStatusTip('Load settings')
        loadSettingsAction.triggered.connect(self.loadSettings)

        saveSettingsAction = QtGui.QAction('&Save Settings', self)        
        saveSettingsAction.setShortcut('Ctrl+S')
        saveSettingsAction.setStatusTip('Save settings')
        saveSettingsAction.triggered.connect(self.saveSettings)

        self.menuFile.addAction(loadSettingsAction)
        self.menuFile.addAction(saveSettingsAction)

        self.var_selector = QtGui.QTreeWidget()
        self.var_selector.setHeaderLabels(["Tree"])
        self.var_selector.itemChanged.connect(self.handleVarSelectorChanged)
        self.var_selector.itemSelectionChanged.connect(self.selectedItemChanged)

        self.thresh_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.thresh_slider.setRange(0, 100)
        self.thresh_slider.setSingleStep(1)
        self.thresh_slider.setTickInterval(100)
        self.thresh_slider.setTickPosition(QtGui.QSlider.TicksRight)
        self.thresh_slider.valueChanged.connect(self.set_thresh_slider_value)
        self.thresh_slider_changed.connect(self.thresh_slider.setValue)
        self.thresh_slider.setValue(100)

        self.size_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.size_slider.setRange(0, 100)
        self.size_slider.setSingleStep(1)
        self.size_slider.setTickInterval(100)
        self.size_slider.setTickPosition(QtGui.QSlider.TicksRight)
        self.size_slider.valueChanged.connect(self.set_size_slider_value)
        self.size_slider_changed.connect(self.size_slider.setValue)
        self.size_slider.setValue(100)

        self.var_info = QtGui.QTextBrowser()
        self.var_info.setCurrentFont(QtGui.QFont('Monospace'))
        self.var_info.setFontPointSize(8)

        ui_pick_colour = QtGui.QPushButton('Pick Colour')
        ui_pick_colour.clicked.connect(self.pick_colour)

	self.ui_thresh = QtGui.QLabel()
	self.ui_thresh.setFixedWidth(50)
	self.ui_size = QtGui.QLabel()
	self.ui_size.setFixedWidth(50)

        lhs_bpanel = QtGui.QWidget()
        lhs_blayout = QtGui.QGridLayout()
        lhs_blayout.addWidget(self.thresh_slider, 0, 0)
        lhs_blayout.addWidget(self.ui_thresh, 0, 1)
        lhs_blayout.addWidget(self.size_slider, 1, 0)
        lhs_blayout.addWidget(self.ui_size, 1, 1)
        lhs_blayout.addWidget(self.var_info, 2, 0, 1, 2)
        lhs_bpanel.setLayout(lhs_blayout)
        lhs_vsplitter = QtGui.QSplitter()
        lhs_vsplitter.setOrientation(QtCore.Qt.Vertical)
        lhs_vsplitter.addWidget(self.var_selector)
        lhs_vsplitter.addWidget(lhs_bpanel)
        lhs_vsplitter.addWidget(ui_pick_colour)

        self.view = gl.GLViewWidget()
        self.view.opts['distance'] = 64
        # Add a grid.
        grid = gl.GLGridItem()
        # TODO: these need to be calculated properly.
        if self.data_source == 'MONC':
            grid.setSize(96, 96, 0)
            grid.setSpacing(4, 4, 0)

            zgrid = gl.GLGridItem()
            zgrid.setSize(96, 48, 0)
            zgrid.rotate(90, 1, 0, 0)
            zgrid.translate(0, -48, 24)
            zgrid.setSpacing(4, 4, 0)

            zgrid2 = gl.GLGridItem()
            zgrid2.setSize(48, 96, 0)
            zgrid2.rotate(90, 0, 1, 0)
            zgrid2.translate(-48, 0, 24)
            zgrid2.setSpacing(4, 4, 0)
        else:
            grid.setSize(64, 64, 0)
            grid.setSpacing(4, 4, 0)

            zgrid = gl.GLGridItem()
            zgrid.setSize(64, 32, 0)
            zgrid.rotate(90, 1, 0, 0)
            zgrid.translate(0, -32, 16)
            zgrid.setSpacing(4, 4, 0)

            zgrid2 = gl.GLGridItem()
            zgrid2.setSize(32, 64, 0)
            zgrid2.rotate(90, 0, 1, 0)
            zgrid2.translate(-32, 0, 16)
            zgrid2.setSpacing(4, 4, 0)

        self.view.addItem(grid)
        self.view.addItem(zgrid)
        self.view.addItem(zgrid2)

        play_controls = QtGui.QWidget()
        play_controls_layout = QtGui.QGridLayout()
        play_controls.setLayout(play_controls_layout)
        play_controls.setFixedHeight(100)

        ui_back = QtGui.QPushButton('Back')
        ui_pause = QtGui.QPushButton('Pause')
        ui_play = QtGui.QPushButton('Play')
        ui_fwd = QtGui.QPushButton('Fwd')

        self.ui_timeout = QtGui.QLineEdit(str(self.timeout))
        self.ui_time_index = QtGui.QLineEdit(str(self.time_index))
        ui_go = QtGui.QPushButton('Go')
        self.ui_loop = QtGui.QCheckBox('Loop')

        ui_back.clicked.connect(self.back)
        ui_pause.clicked.connect(self.pause)
        ui_play.clicked.connect(self.play)
        ui_fwd.clicked.connect(self.fwd)
        ui_go.clicked.connect(self.go)

        self.time_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        play_controls_layout.addWidget(self.time_slider, 0, 0, 1, 4)
        play_controls_layout.addWidget(ui_back, 1, 0)
        play_controls_layout.addWidget(ui_pause, 1, 1)
        play_controls_layout.addWidget(ui_play, 1, 2)
        play_controls_layout.addWidget(ui_fwd, 1, 3)
        play_controls_layout.addWidget(self.ui_timeout, 2, 0)
        play_controls_layout.addWidget(self.ui_time_index, 2, 1)
        play_controls_layout.addWidget(ui_go, 2, 2)
        play_controls_layout.addWidget(self.ui_loop, 2, 3)

        middle = QtGui.QWidget()
        middle_size_policy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        middle_size_policy.setHorizontalStretch(3)
        middle.setSizePolicy(middle_size_policy)

        middle_layout = QtGui.QVBoxLayout()

        middle.setSizePolicy(middle_size_policy)
        middle_layout.addWidget(self.view)
        middle_layout.addWidget(play_controls)
        middle.setLayout(middle_layout)

        main_hsplitter = QtGui.QSplitter()
        main_hsplitter.addWidget(lhs_vsplitter)
        main_hsplitter.addWidget(middle)

        main_layout = QtGui.QHBoxLayout()
        main_layout.addWidget(main_hsplitter)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
