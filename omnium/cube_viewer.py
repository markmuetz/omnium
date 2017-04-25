from collections import namedtuple

import iris

from omnium.data_displays.twod_window import TwodWindow

class DispSetting(object):
    def __init__(self, time_index, level_index):
        self.time_index = time_index
        self.level_index = level_index


class CubeViewer(object):
    def __init__(self, cube, display):
        self.cube = cube
        self.display = display
        if cube.ndim == 4:
            level_index = 0
        else:
            level_index = None
        self.setting = DispSetting(0, level_index)

    @property
    def time_index(self):
        return self.setting.time_index

    @time_index.setter
    def time_index(self, value):
        if value < 0 or value >= self.cube.shape[0]:
            raise ValueError('Value is out of range (0, {})'.format(self.cube.shape[0] - 1))
        self.setting.time_index = value

    @property
    def level_index(self):
        return self.setting.level_index

    @level_index.setter
    def level_index(self, value):
        if value < 0 or value >= self.cube.shape[1]:
            raise ValueError('Value is out of range (0, {})'.format(self.cube.shape[1] - 1))
        self.setting.level_index = value

    def show(self):
        if self.display.isHidden():
            self.display.show()
        self.display.setData(self.cube[self.time_index, self.level_index].data)


class CubeListViewer(object):
    def __init__(self):
        self._cubes = None
        self._viewers = []
        self.time_index = 0
        self.level_index = 0

    def load(self, filenames):
        print('Loading: {}'.format(filenames))
        self._cubes = iris.load(filenames).concatenate()

    def add_disp(self, index, disp_type='2d'):
        if disp_type == '2d':
            display = TwodWindow()

        self._viewers.append(CubeViewer(self._cubes[index], display))

    def show(self):
        for viewer in self._viewers:
            viewer.time_index = self.time_index
            viewer.level_index = self.level_index
            viewer.show()

    def next(self):
        self.go(self.time_index + 1)

    def prev(self):
        self.go(self.time_index - 1)

    def up(self):
        self.go(level_index=self.level_index + 1)

    def down(self):
        self.go(level_index=self.level_index - 1)
    
    def go(self, time_index=None, level_index=None):
        'go to specified time_index'
        if time_index is not None:
            self.time_index = time_index
        if level_index is not None:
            self.level_index = level_index

        self.show()

