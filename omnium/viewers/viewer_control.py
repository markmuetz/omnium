import os
import re
import pickle
from collections import OrderedDict
from logging import getLogger

from pyqtgraph.Qt import QtCore, QtGui
from omnium.viewers.data_displays import (TwodWindow, ThreedWindow,
                                          PlotWindow, ProfileWindow, ProfileContourWindow)
from omnium import Stash

import iris

logger = getLogger('omnium')

MAP_NAME_TO_CLASS = OrderedDict([
    ('Slice', TwodWindow),
    ('3D', ThreedWindow),
    ('Plot', PlotWindow),
    ('Profile', ProfileWindow),
    ('Contour', ProfileContourWindow),
])


class ViewerControlWindow(QtGui.QMainWindow):
    time_slider_changed = QtCore.pyqtSignal(int)

    def __init__(self, state, filenames):
        super(ViewerControlWindow, self).__init__()
        # super(ViewerControlWindow, self).__init__(None, QtCore.Qt.WindowStaysOnTopHint)
        self.filenames = filenames
        self.cubes = OrderedDict()
        self.time_index = 0
        self.wins = []
        self.stash = Stash()
        self.times = []

        self.setupGui()
        if not state and self.filenames:
            self.addVarItems(self.filenames)

        # self.time_slider.setRange(0, self.cube_list_viewer.cubes[0].shape[0])
        self.time_slider.setSingleStep(1)
        self.time_slider.setPageStep(15)
        self.time_slider.setTickInterval(60)
        self.time_slider.setTickPosition(QtGui.QSlider.TicksRight)
        self.time_slider.valueChanged.connect(self.setTimeSliderValue)
        self.time_slider_changed.connect(self.time_slider.setValue)

        self.timer = QtCore.QTimer(self)
        self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.fwd)

        if state:
            self.loadState(state)

    def saveState(self):
        state = {}
        state['pos'] = self.pos()
        state['size'] = self.size()
        state['time_index'] = self.time_index
        state['filenames'] = self.filenames
        state['child_windows'] = []
        for win in self.wins:
            if win.isVisible():
                win_state = win.saveState()
                win_state['cubes'] = []
                if win.accepts_multiple_cubes:
                    for cube in win.cubes:
                        for stream in self.cubes.keys():
                            if cube in self.cubes[stream]:
                                win_state['cubes'].append((stream, cube.name()))
                else:
                    # import ipdb; ipdb.set_trace()
                    cube = win.cube
                    for stream in self.cubes.keys():
                        if cube in self.cubes[stream]:
                            win_state['cubes'].append((stream, cube.name()))

                state['child_windows'].append(win_state)

        filename = QtGui.QFileDialog.getSaveFileName(self, 'Save State',
                                                     os.getcwd(), selectedFilter='*.pkl')
        if filename:
            with open(filename, 'w') as f:
                pickle.dump(state, f)

    def loadState(self, state_filename=None):
        if not state_filename:
            filename = QtGui.QFileDialog.getOpenFileName(self, 'Load State',
                                                         os.getcwd(), 'State files (*.pkl)')

            if not filename:
                return
        filename = state_filename
        with open(filename, 'r') as f:
            state = pickle.load(f)

        self.move(state['pos'])
        self.resize(state['size'])
        self.filenames = state['filenames']
        self.time_index = state['time_index']

        self.time_slider_changed.emit(self.time_index)

        for win in self.wins:
            win.close()
        self.wins = []

        if self.filenames:
            self.cubes = OrderedDict()
            self.addVarItems(self.filenames)

        for win_state in state['child_windows']:
            print(win_state)
            cubes = []
            for stream, cube_name in win_state['cubes']:
                for cube in self.cubes[stream]:
                    if cube_name == cube.name():
                        cubes.append(cube)
                        break

            Cls = MAP_NAME_TO_CLASS[win_state['name']]
            if Cls.accepts_multiple_cubes:
                win = Cls(self)
                win.loadState(win_state)
                win.setupGui()
                win.setCubes(cubes)
                win.setTime(self.times[self.time_index])
                win.show()
                self.wins.append(win)
            else:
                win = Cls(self)
                win.loadState(win_state)
                win.setupGui()
                win.setCube(cubes[0])
                win.setTime(self.times[self.time_index])
                win.show()
                self.wins.append(win)

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

    def setTimeSliderValue(self, value):
        self.time_index = value
        self.ui_time_index.setText(str(self.time_index))
        for win in self.wins:
            win.setTime(self.times[self.time_index])
            # win.time_index = self.time_index

        for win in self.wins:
            win.update()

    def launch(self):
        cubes = []
        for item in self.var_selector.selectedItems():
            data = item.data(0, QtCore.Qt.UserRole)
            cube = data.toPyObject()
            # cube = self.cubes[index]
            cubes.append(cube)

        cb = self.ui_displays
        # import ipdb; ipdb.set_trace()

        display_name = str(self.ui_displays.currentText())

        Cls = MAP_NAME_TO_CLASS[display_name]
        if Cls.accepts_multiple_cubes:
            win = Cls(self)
            win.setupGui()
            win.setCubes(cubes)
            win.setTime(self.times[self.time_index])
            win.show()
            self.wins.append(win)
        else:
            for cube in cubes:
                win = Cls(self)
                win.setupGui()
                win.setCube(cube)
                win.setTime(self.times[self.time_index])
                win.show()
                self.wins.append(win)

    def addCube(self, parent, cube):
        cube_name = ' '.join(cube.name().split())
        if cube.ndim < 2:
            logger.info('Cube {} only has {} dim(s) - not adding'.format(cube_name, cube.ndim))
            return

        nt = str(cube.shape[0])
        nx = str(cube.shape[-2])
        ny = str(cube.shape[-1])
        if cube.ndim == 4:
            nz = str(cube.shape[1])
        else:
            nz = ''
        cube_item = QtGui.QTreeWidgetItem(parent, [cube_name, nt, nz, nx, ny])
        cube_item.setData(0, QtCore.Qt.UserRole, cube)
        self.updateTimes(cube)

    def updateTimes(self, cube):
        new_times = cube.coord('time').points
        # import ipdb; ipdb.set_trace()
        if len(self.times) and (new_times[0] > self.times[-1] or new_times[-1] < self.times[0]):
            print('WARNING: times do not overlap')
        if len(new_times) > len(self.times):
            print('Using new times from {}: len {}'.format(cube.name(), len(new_times)))
            self.times = new_times
            self.time_slider.setRange(0, len(self.times) - 1)

    def matchFilename(self, filename):
        match = re.match('atmos.(?P<hours>\d{3}).(?P<stream>pp\d{1})(?P<ext>\.nc|)', filename)

        if match:
            return match.groups()
        else:
            match = re.match('atmos.(?P<stream>pp\d{1})(?P<ext>\.nc|)', filename)
            if match:
                return (None, match.group('stream'), match.group('ext'))
            else:
                return (None, 'default', '.nc')

    def addFile(self, filename):
        print(filename)
        fn = os.path.basename(filename)
        hours, stream, ext = self.matchFilename(fn)

        new_cubes = iris.load(filename)

        # self.stash.rename_unknown_cubes(new_cubes, True)

        if stream in self.cubes:
            self.cubes[stream].extend(new_cubes)
            self.cubes[stream] = self.cubes[stream].concatenate()
        else:
            self.cubes[stream] = new_cubes

    def addVarItems(self, filenames):
        for filename in filenames:
            self.addFile(filename)

        self.var_selector.clear()
        self.times = []

        root = self.var_selector.invisibleRootItem()
        for stream, cubes in self.cubes.items():
            stream_item = QtGui.QTreeWidgetItem(root, [stream])
            stream_item.setExpanded(True)
            for cube in cubes:
                self.addCube(stream_item, cube)

    def selectedItemChanged(self):
        print('selectedItemChanged')

    def handleVarSelectorChanged(self, item, column):
        pass

    def open(self):
        dlg = QtGui.QFileDialog(self, 'Open Cubes', os.getcwd())
        dlg.setFileMode(QtGui.QFileDialog.ExistingFiles)
        dlg.setFilter("Cube files (*.nc *.pp?)")
        dlg.setFilter
        filenames = []
        if dlg.exec_():
            for filename in dlg.selectedFiles():
                filenames.append(str(filename))
            print(filenames)
            self.filenames.extend(filenames)
            self.addVarItems(filenames)

    def setupGui(self):
        self.resize(400, 600)
        central_widget = QtGui.QWidget()

        self.menubar = QtGui.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(20, 20, 800, 23))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtGui.QMenu(self.menubar)
        self.menuFile.setTitle("File")
        self.menubar.addAction(self.menuFile.menuAction())
        self.setMenuBar(self.menubar)

        openAction = QtGui.QAction('&Open Cubes', self)
        openAction.setShortcut('Ctrl+O')
        openAction.triggered.connect(self.open)

        loadStateAction = QtGui.QAction('&Load State', self)
        loadStateAction.setShortcut('Ctrl+L')
        loadStateAction.setStatusTip('Load settings')
        loadStateAction.triggered.connect(self.loadState)

        saveStateAction = QtGui.QAction('&Save State', self)
        saveStateAction.setShortcut('Ctrl+S')
        saveStateAction.setStatusTip('Save settings')
        saveStateAction.triggered.connect(self.saveState)

        self.menuFile.addAction(openAction)
        self.menuFile.addAction(loadStateAction)
        self.menuFile.addAction(saveStateAction)

        play_controls = QtGui.QWidget()
        play_controls_layout = QtGui.QGridLayout()
        play_controls.setLayout(play_controls_layout)
        play_controls.setFixedHeight(100)

        ui_back = QtGui.QPushButton('Back')
        ui_pause = QtGui.QPushButton('Pause')
        ui_play = QtGui.QPushButton('Play')
        ui_fwd = QtGui.QPushButton('Fwd')

        self.ui_timeout = QtGui.QLineEdit(str(200))
        self.ui_time_index = QtGui.QLineEdit(str(0))
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

        self.var_selector = QtGui.QTreeWidget()
        self.var_selector.setHeaderLabels(['Name', 'nt', 'nz', 'nx', 'ny'])
        self.var_selector.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.var_selector.itemSelectionChanged.connect(self.selectedItemChanged)
        self.ui_displays = QtGui.QComboBox()

        for name in MAP_NAME_TO_CLASS.keys():
            self.ui_displays.addItem(name)

        ui_launch = QtGui.QPushButton('Launch')
        ui_launch.clicked.connect(self.launch)
        cube_widget = QtGui.QWidget()
        cube_widget_layout = QtGui.QVBoxLayout()
        cube_widget_layout.addWidget(self.var_selector)
        cube_widget_layout.addWidget(self.ui_displays)
        cube_widget_layout.addWidget(ui_launch)
        cube_widget.setLayout(cube_widget_layout)

        lhs_vsplitter = QtGui.QSplitter()
        lhs_vsplitter.setOrientation(QtCore.Qt.Vertical)
        lhs_vsplitter.addWidget(play_controls)
        lhs_vsplitter.addWidget(cube_widget)

        main_hsplitter = QtGui.QSplitter()
        main_hsplitter.addWidget(lhs_vsplitter)

        main_layout = QtGui.QHBoxLayout()
        main_layout.addWidget(main_hsplitter)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
