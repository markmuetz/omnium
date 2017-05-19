from pyqtgraph.Qt import QtGui
import pyqtgraph as pg

from omnium.viewers.data_displays import DataDisplayWindow


class ProfileWindow(DataDisplayWindow):
    name = 'Plot'
    title = 'Plot Display'
    accepts_multiple_cubes = True

    def setupGui(self):
        super(ProfileWindow, self).setupGui()
        self.resize(400, 300)
        self.plotWidget = pg.PlotWidget(self)

        lhs_hsplitter = QtGui.QSplitter()
        lhs_hsplitter.addWidget(self.plotWidget)

        self.main_layout.addWidget(lhs_hsplitter)
        self.plots = {}
        self.data = []

    def setCubes(self, cubes):
        # Check all cubes have the same time dimension.
        assert len(set([c.shape[0] for c in cubes])) == 1
        self.cubes = cubes
        self.cube = cubes[0]
        for cube in self.cubes:
            if cube.ndim != 4:
                msg = 'Two few or too many dims: {} - {}'.format(cube.name(), cube.ndim)
                raise Exception(msg)

        for cube in self.cubes:
            heights = cube.coord('level_height').points
            self.data.append((cube.name(), heights, cube.data.mean(axis=(2, 3))))
        self.update()

    def update(self):
        # self.plotWidget.clear()
        for name, heights, data in self.data:
            if name not in self.plots:
                plot = self.plotWidget.plot(data[self.time_index], heights)
                self.plots[name] = plot
            else:
                plot = self.plots[name]
                plot.setData(data[self.time_index], heights)
