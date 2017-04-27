import os

from pyqtgraph.Qt import QtCore, QtGui
from omnium.data_displays import TwodWindow, ThreedWindow, PlotWindow

import iris

class ViewerControlWindow(QtGui.QMainWindow):
    time_slider_changed = QtCore.pyqtSignal(int)

    def __init__(self, filenames):
        super(ViewerControlWindow, self).__init__()
        self.filenames = filenames
        self.cubes = []
        self.time_index = 0
        self.wins = []

        self.setupGui()
        self.addVarItems()

        #self.time_slider.setRange(0, self.cube_list_viewer.cubes[0].shape[0])
        self.time_slider.setRange(0, 95)
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

    def set_time_slider_value(self, value):
        self.time_index = value
        self.ui_time_index.setText(str(self.time_index))
        for win in self.wins:
            win.time_index = self.time_index
            win.update()

    def launch(self):
        cubes = []
        for item in self.var_selector.selectedItems():
            data = item.data(0, QtCore.Qt.UserRole)
            index = data.toPyObject()
            cube = self.cubes[index]
            cubes.append(cube)

        cb = self.ui_displays
        #import ipdb; ipdb.set_trace()

        display_name = str(self.ui_displays.currentText())
        if display_name in ['Slice']:
            for cube in cubes:
                if display_name == 'Slice':
                    win = TwodWindow(self)
                win.setData(cube)
                win.show()
                self.wins.append(win)

        elif display_name in ['3D', 'Plot']:
            if display_name == '3D':
                win = ThreedWindow(self)
            elif display_name == 'Plot':
                win = PlotWindow(self)
            win.setData(cubes)
            win.show()
            self.wins.append(win)

    def addCube(self, parent, cube):
        cube_name = ' '.join(cube.name().split())
        cube_item = QtGui.QTreeWidgetItem(parent, [cube_name])
        cube_item.setData(0, QtCore.Qt.UserRole, len(self.cubes))
        #cube_item.setCheckState(0, QtCore.Qt.Unchecked)
        self.cubes.append(cube)

    def addFile(self, root, filename):
        print(filename)
        fn = os.path.basename(filename)
        file_item = QtGui.QTreeWidgetItem(root, [fn])
        #file_item.setChildIndicatorPolicy(QtGui.QTreeWidgetItem.ShowIndicator)
        #file_item.setData(0, QtCore.Qt.UserRole, fn)
        file_item.setExpanded(True)
        cubes = iris.load(filename)

        #if self.data_source == 'UM':
            #self.stash.rename_unknown_cubes(cubes, True)
        
        for i, cube in enumerate(cubes):
            self.addCube(file_item, cube)

    def addVarItems(self):
        root = self.var_selector.invisibleRootItem()
        for filename in self.filenames:
            self.addFile(root, filename)
        # Do this after items have been added.
        self.var_selector.itemChanged.connect(self.handleVarSelectorChanged)


    def handleVarSelectorChanged(self, item, column):
        if self.cubes:
            data = item.data(column, QtCore.Qt.UserRole)
            if item.checkState(column) == QtCore.Qt.Checked:
                index = data.toPyObject()
                cube = self.cubes[index]
                print(cube.name())
                print('checked')

            elif item.checkState(column) == QtCore.Qt.Unchecked:
                index = data.toPyObject()
                cube = self.cubes[index]
                print(cube.name())
                print('unchecked')


    def selectedItemChanged(self):
        print('selectedItemChanged')


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

        loadSettingsAction = QtGui.QAction('&Load Settings', self)        
        loadSettingsAction.setShortcut('Ctrl+L')
        loadSettingsAction.setStatusTip('Load settings')
        #loadSettingsAction.triggered.connect(self.loadSettings)

        saveSettingsAction = QtGui.QAction('&Save Settings', self)        
        saveSettingsAction.setShortcut('Ctrl+S')
        saveSettingsAction.setStatusTip('Save settings')
        #saveSettingsAction.triggered.connect(self.saveSettings)

        self.menuFile.addAction(loadSettingsAction)
        self.menuFile.addAction(saveSettingsAction)

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
        self.var_selector.setHeaderLabels(["Tree"])
        self.var_selector.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.var_selector.itemSelectionChanged.connect(self.selectedItemChanged)
        self.ui_displays = QtGui.QComboBox()
        self.ui_displays.addItem('Slice')
        self.ui_displays.addItem('3D')
        self.ui_displays.addItem('Plot')

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
