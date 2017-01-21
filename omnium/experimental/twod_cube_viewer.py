import os
from collections import namedtuple, OrderedDict
import datetime as dt

import pylab as plt
import iris

DispSetting = namedtuple("DispSetting", ["ignore_first", 'vmax', 'vmin']) 

class TwodCubeViewer(object):
    def __init__(self, start_time=dt.datetime(2012, 9, 27, 21, 5)):
        plt.ion()
        self.cubes = None
        self.displayed_cubes = OrderedDict()
        self.curr_time_index = 0
        self.start_time = start_time

    def load(self, filename):
        filename = os.path.expanduser(filename)
        print(filename)
        self.cubes = iris.load(filename)

    def add_disp(self, index, ignore_first=False):
        cube = self.cubes[index]
        setting = DispSetting(ignore_first, cube.data.max(), cube.data.min())
        self.displayed_cubes[index] = (setting, cube)
        self._check_displayed_cubes()

    def rm_disp(self, index):
        #self.displayed_cubes.append(self.cubes[index])
        pass

    def _check_displayed_cubes(self):
        all_cube_length = None
        for i, (setting, cube) in self.displayed_cubes.items():
            cube_length = cube.shape[0] - 1 if setting.ignore_first else cube.shape[0]
            if not all_cube_length:
                all_cube_length = cube_length
            else:
                if cube_length != all_cube_length:
                    print('Warning, cube length mismatch')
        self.all_cube_length = all_cube_length
            
    def next(self):
        self.curr_time_index += 1
        self.show()

    def prev(self):
        self.curr_time_index -= 1
        self.show()

    def go(self, time_index):
        self.curr_time_index = time_index
        self.show()

    def play(self, length=None, reverse=False, timeout=100):
        while self.curr_time_index < self.all_cube_length and length != 0:
            try:
                if length:
                    length -= 1
                if reverse:
                    self.prev()
                else:
                    self.next()
                plt.pause(timeout / 1000.)
            except KeyboardInterrupt:
                break

    def disp(self):
        for i, cube in enumerate(self.cubes):
            displayed = '*' if i in self.displayed_cubes else ' '
            setting = self.displayed_cubes[i][0] if displayed == '*' else ''
            print('{}: [{}] {}, {}'.format(i, displayed, cube.name(), setting))

    def show(self):
        for i, (setting, cube) in self.displayed_cubes.items():
            if setting.ignore_first:
                curr_time_index = self.curr_time_index + 1
            else:
                curr_time_index = self.curr_time_index

            plt.figure(cube.name())
            plt.clf()
            time_hrs_since_19700101 = cube.coord('time').points[curr_time_index]
            time = dt.datetime(1970, 1, 1) + dt.timedelta(0, time_hrs_since_19700101 * 3600)
            elapsed_time = time - self.start_time

            plt.title('{0}: {1:1.2}'.format(curr_time_index, elapsed_time.seconds/86400.) )
            plt.imshow(cube.data[curr_time_index], interpolation='nearest', origin='lower',
                       vmax=setting.vmax, vmin=setting.vmin)
            plt.pause(0.0001)

if __name__ == '__main__':
    tcv = TwodCubeViewer()
    tcv.load('~/um_output/um10.6_runs/20day/iUM_CC2006_no_wind/work/20000101T0000Z/atmos/atmos.pp1.nc')
    tcv.add_disp(3)
    tcv.add_disp(6, True)
    tcv.go(100)
    tcv.show()
