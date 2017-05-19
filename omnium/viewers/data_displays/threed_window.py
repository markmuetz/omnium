from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.opengl as gl
import numpy as np

from omnium.viewers.data_displays import DataDisplayWindow


class ThreedWindow(DataDisplayWindow):
    name = '3D'
    title = '3D Display'
    accepts_multiple_cubes = True

    thresh_slider_changed = QtCore.pyqtSignal(float)
    neg_thresh_slider_changed = QtCore.pyqtSignal(float)
    size_slider_changed = QtCore.pyqtSignal(float)
    colours = [(1, 1, 1, 1),
               (0, 1, 1, 1),
               (0, 0, 1, 1),
               (1, 0, 1, 1),
               (1, 0.5, 1, 1),
               (1, 0, 0, 1),
               (1, 0.5, 0, 1),
               (1, 1, 0, 1)]

    def __init__(self, parent):
        super(ThreedWindow, self).__init__(parent)
        self.data_source = 'UM'
        self.timeout = 250
        self.cube_index = None

        self.rendered_point_scatters = {}
        self.point_scatters = {}
        self.cube_settings = {}
        self.cubes = []
        self.zn = None
        self.thresh = 0.
        self.neg_thresh = 0.

    def saveState(self):
        state = super(ThreedWindow, self).saveState()
        state['camera_position'] = tuple(self.view.cameraPosition())
        return state

    def loadState(self, state):
        super(ThreedWindow, self).loadState(state)

    def pick_colour(self):
        if self.cube_index is not None:
            colour = QtGui.QColorDialog.getColor().getRgbF()
            self.cube_settings[self.cube_index]['colour'] = colour

            self.point_scatters.pop(self.cube_index)
            self.point_scatters.pop(self.cube_index + 9999)
            self.add_remove()
            self.add_cube(self.cube_index)
            self.add_remove()

    def set_thresh_slider_value(self, value):
        frac = value / 1000.
        print(frac)
        if self.cube_index is not None and (self.cube_index in self.rendered_point_scatters or
                                            self.cube_index + 9999 in self.rendered_point_scatters):
            cube = self.cubes[self.cube_index]
            thresh = 20 * frac
            print(thresh)
            self.cube_settings[self.cube_index]['thresh'] = thresh

            self.point_scatters.pop(self.cube_index)
            self.point_scatters.pop(self.cube_index + 9999)
            self.add_remove()
            self.add_cube(self.cube_index)
            self.add_remove()
            self.ui_thresh.setText('{0:.3f}'.format(thresh))

    def set_neg_thresh_slider_value(self, value):
        frac = (1000 - value) / 1000.
        if self.cube_index is not None and (self.cube_index in self.rendered_point_scatters or
                                            self.cube_index + 9999 in self.rendered_point_scatters):
            cube = self.cubes[self.cube_index]
            neg_thresh = -20 * frac
            self.cube_settings[self.cube_index]['neg_thresh'] = neg_thresh

            self.point_scatters.pop(self.cube_index)
            self.point_scatters.pop(self.cube_index + 9999)
            self.add_remove()
            self.add_cube(self.cube_index)
            self.add_remove()
            self.ui_neg_thresh.setText('{0:.3f}'.format(neg_thresh))

    def set_size_slider_value(self, value):
        if self.cube_index is not None and self.cube_index in self.rendered_point_scatters:
            cube = self.cubes[self.cube_index]
            self.cube_settings[self.cube_index]['size_scale'] = value

            self.point_scatters.pop(self.cube_index)
            self.point_scatters.pop(self.cube_index + 9999)
            self.add_remove()
            self.add_cube(self.cube_index)
            self.add_remove()
            self.ui_size.setText('{0:.3f}'.format(value))

    def addCube(self, parent, cube):
        cube_name = ' '.join(cube.name().split())
        cube_item = QtGui.QTreeWidgetItem(parent, [cube_name])
        cube_item.setData(0, QtCore.Qt.UserRole, len(self.cubes))
        cube_item.setCheckState(0, QtCore.Qt.Unchecked)
        self.cubes.append(cube)

    def setCubes(self, cubes):
        # Check all cubes have the same time dimension.
        assert len(set([c.shape[0] for c in cubes])) == 1

        self.cube = cubes[0]
        root = self.var_selector.invisibleRootItem()
        for cube in cubes:
            assert cube.ndim == 4
            self.addCube(root, cube)

    def get_pos_size(self, cube, thresh, size_scale, neg=False):
        if neg:
            d = (cube.data < thresh)
        else:
            d = (cube.data > thresh)
        print(neg)
        print(cube.shape)

        # Get value of array where comparison is True.
        # size = cube.data[d] * multiplier
        size = 5
        if self.data_source == 'UM':
            # Needs some unpacking:
            # np.where(d) gets indices where comparison is true, but needs transposed.
            # indices are currently in order z, x, y, np.roll fixes this.
            pos_indices = np.roll(np.array(np.where(d)).T, -1, axis=1)

            # Map indices to values.
            pos = np.empty_like(pos_indices, dtype=np.float64)
            pos[:, 0] = -cube.coord('grid_longitude')\
                             .points[pos_indices[:, 0]] / 1000
            pos[:, 1] = cube.coord('grid_latitude')\
                            .points[pos_indices[:, 1]] / 1000
            pos[:, 2] = cube.coord('level_height')\
                            .points[pos_indices[:, 2]] / 1000

            pos -= [-128, 128, 0]
            print(pos.shape)
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

    def update(self):
        print('updating')
        old_point_scatters_keys = self.point_scatters.keys()
        self.point_scatters = {}
        self.add_remove()
        for cube_index in old_point_scatters_keys:
            if cube_index < 9999:
                self.add_cube(cube_index)
        self.add_remove()

    def add_remove(self):
        for index in self.point_scatters.keys():
            if index not in self.rendered_point_scatters:
                print('adding {}'.format(index))
                point_scatter = self.point_scatters[index]
                self.view.addItem(point_scatter)
                self.rendered_point_scatters[index] = point_scatter

        for index in self.rendered_point_scatters.keys():
            if index not in self.point_scatters:
                print('removing {}'.format(index))
                point_scatter = self.rendered_point_scatters.pop(index)
                self.view.removeItem(point_scatter)

    def add_cube(self, cube_index):
        cube = self.cubes[cube_index]
        thresh = self.cube_settings[cube_index]['thresh']
        neg_thresh = self.cube_settings[cube_index]['neg_thresh']
        colour = self.cube_settings[cube_index]['colour']
        size_scale = self.cube_settings[cube_index]['size_scale']
        # cube_max = self.cube_settings[cube_index]['cube_max']

        pos, size = self.get_pos_size(cube[self.time_index], thresh, size_scale)
        point_scatter = gl.GLScatterPlotItem(pos=pos, color=(1, 0, 0, 1), size=size)
        point_scatter.setGLOptions('opaque')
        self.point_scatters[cube_index] = point_scatter

        pos, size = self.get_pos_size(cube[self.time_index], neg_thresh, size_scale, neg=True)
        point_scatter = gl.GLScatterPlotItem(pos=pos, color=(0, 0, 1, 1), size=size)
        point_scatter.setGLOptions('opaque')
        self.point_scatters[cube_index + 9999] = point_scatter

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
                self.cube_settings[index]['thresh'] = 1
                self.cube_settings[index]['neg_thresh'] = -1
                self.cube_settings[index]['size_scale'] = 5
                # self.cube_settings[index]['cube_max'] = cube.data.max()
            # Initial scatter.
            self.add_cube(index)
            self.add_remove()

        elif item.checkState(column) == QtCore.Qt.Unchecked:
            index = data.toPyObject()
            if index in self.point_scatters:
                self.point_scatters.pop(index)
                if index + 9999 in self.point_scatters:
                    self.point_scatters.pop(index + 9999)
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
            # frac = thresh / cube.data.max()
            frac = thresh / 20
            value = 1000 * frac
            self.thresh_slider_changed.emit(value)
        if 'size_scale' in self.cube_settings[index]:
            size_scale = self.cube_settings[index]['size_scale']
            self.size_slider_changed.emit(size_scale)

    def setupGui(self):
        super(ThreedWindow, self).setupGui()

        self.resize(800, 600)

        self.var_selector = QtGui.QTreeWidget()
        self.var_selector.setHeaderLabels(["Tree"])
        self.var_selector.itemChanged.connect(self.handleVarSelectorChanged)
        self.var_selector.itemSelectionChanged.connect(self.selectedItemChanged)

        self.thresh_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.thresh_slider.setRange(0, 1000)
        self.thresh_slider.setSingleStep(1)
        self.thresh_slider.setTickInterval(1000)
        self.thresh_slider.setTickPosition(QtGui.QSlider.TicksRight)
        self.thresh_slider.valueChanged.connect(self.set_thresh_slider_value)
        self.thresh_slider_changed.connect(self.thresh_slider.setValue)
        self.thresh_slider.setValue(1000)

        self.neg_thresh_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.neg_thresh_slider.setRange(0, 1000)
        self.neg_thresh_slider.setSingleStep(1)
        self.neg_thresh_slider.setTickInterval(1000)
        self.neg_thresh_slider.setTickPosition(QtGui.QSlider.TicksRight)
        self.neg_thresh_slider.valueChanged.connect(self.set_neg_thresh_slider_value)
        self.neg_thresh_slider_changed.connect(self.neg_thresh_slider.setValue)
        self.neg_thresh_slider.setValue(1000)

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
        self.ui_neg_thresh = QtGui.QLabel()
        self.ui_neg_thresh.setFixedWidth(50)
        self.ui_size = QtGui.QLabel()
        self.ui_size.setFixedWidth(50)

        lhs_bpanel = QtGui.QWidget()
        lhs_blayout = QtGui.QGridLayout()
        lhs_blayout.addWidget(self.thresh_slider, 0, 0)
        lhs_blayout.addWidget(self.ui_thresh, 0, 1)
        lhs_blayout.addWidget(self.neg_thresh_slider, 1, 0)
        lhs_blayout.addWidget(self.ui_neg_thresh, 1, 1)

        lhs_blayout.addWidget(self.var_info, 2, 0, 1, 2)
        lhs_bpanel.setLayout(lhs_blayout)
        lhs_vsplitter = QtGui.QSplitter()
        lhs_vsplitter.setOrientation(QtCore.Qt.Vertical)
        lhs_vsplitter.addWidget(self.var_selector)
        lhs_vsplitter.addWidget(lhs_bpanel)
        lhs_vsplitter.addWidget(ui_pick_colour)

        self.view = gl.GLViewWidget()
        self.view.opts['distance'] = 256
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
            grid.setSize(256, 256, 0)
            grid.setSpacing(16, 16, 0)

            zgrid = gl.GLGridItem()
            zgrid.setSize(256, 32, 0)
            zgrid.rotate(90, 1, 0, 0)
            zgrid.translate(0, -128, 16)
            zgrid.setSpacing(16, 16, 0)

            zgrid2 = gl.GLGridItem()
            zgrid2.setSize(32, 256, 0)
            zgrid2.rotate(90, 0, 1, 0)
            zgrid2.translate(-128, 0, 16)
            zgrid2.setSpacing(16, 16, 0)

        self.view.addItem(grid)
        self.view.addItem(zgrid)
        self.view.addItem(zgrid2)

        self.ui_timeout = QtGui.QLineEdit(str(self.timeout))
        self.ui_time_index = QtGui.QLineEdit(str(self.time_index))
        ui_go = QtGui.QPushButton('Go')
        self.ui_loop = QtGui.QCheckBox('Loop')

        middle = QtGui.QWidget()
        middle_size_policy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        middle_size_policy.setHorizontalStretch(3)
        middle.setSizePolicy(middle_size_policy)

        middle_layout = QtGui.QVBoxLayout()

        middle.setSizePolicy(middle_size_policy)
        middle_layout.addWidget(self.view)
        middle.setLayout(middle_layout)

        main_hsplitter = QtGui.QSplitter()
        main_hsplitter.addWidget(lhs_vsplitter)
        main_hsplitter.addWidget(middle)
        self.main_layout.addWidget(main_hsplitter)
