from pyqtgraph.Qt import QtGui
import pyqtgraph as pg

from omnium.viewers.data_displays import DataDisplayWindow


class PlotWindow(DataDisplayWindow):
    name = 'Plot'
    title = 'Plot Display'
    accepts_multiple_cubes = True

    def setupGui(self):
        super(PlotWindow, self).setupGui()
        self.resize(400, 300)
        self.plotWidget = pg.PlotWidget(self)

        lhs_hsplitter = QtGui.QSplitter()
        lhs_hsplitter.addWidget(self.plotWidget)

        self.main_layout.addWidget(lhs_hsplitter)

    def setCubes(self, cubes):
        # Check all cubes have the same time dimension.
        assert len(set([c.shape[0] for c in cubes])) == 1
        self.cubes = cubes
        self.cube = cubes[0]

        for cube in cubes:
            if cube.ndim == 3:
                self.plotWidget.plot(range(cube.shape[0]), cube.data.mean(axis=(1, 2)))
            elif cube.ndim == 4:
                self.plotWidget.plot(range(cube.shape[0]), cube.data.mean(axis=(1, 2, 3)))
            elif cube.ndim == 5:
                self.plotWidget.plot(range(cube.shape[0]), cube.data.mean(axis=(1, 2, 3, 4)))
            else:
                msg = 'Two few or too many dims: {} - {}'.format(cube.name(), cube.ndim)
                raise Exception(msg)
        self.time_line = pg.InfiniteLine(movable=False, angle=90, label='t={value:0.2f}',
                                         labelOpts={'position': 0.1, 'color': (200, 200, 100),
                                                    'fill': (200, 200, 200, 50), 'movable': True})
        self.plotWidget.addItem(self.time_line)
        self.update()

    def update(self):
        self.time_line.setPos(self.time_index)
