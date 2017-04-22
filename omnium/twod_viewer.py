import os
from collections import namedtuple, OrderedDict
import datetime as dt
import pickle
from glob import glob
import warnings

import numpy as np
import iris

from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg

import omnium

DispSetting = namedtuple('DispSetting', ['disp', 'ignore_first', 'map_index', 'vmax', 'vmin']) 
State = namedtuple('State', ['curr_time_index']) 

STASH = omnium.Stash()
# Fixes:
# iris/fileformats/cf.py:1140: IrisDeprecation: NetCDF default loading behaviour...
# warning message.
iris.FUTURE.netcdf_promote = True

class ImageWindow(QtGui.QMainWindow):
    def __init__(self):
        super(ImageWindow, self).__init__()
        self._img = pg.ImageItem(border='w')
        self._img.setOpts(axisOrder='row-major')
        glw = pg.GraphicsLayoutWidget()
        view = glw.addViewBox()
        view.addItem(self._img)
        self.setCentralWidget(glw)
        lut = np.zeros((256,3), dtype=np.ubyte)

	pos = np.array([0.0, 
                        0.5, 
			1.0])
	color = np.array([[255,255,255,255], 
                          [255,128,0,255], 
                          [255,255,0,255]], dtype=np.ubyte)
	cmap = pg.ColorMap(pos, color)
	lut = cmap.getLookupTable(0.0, 1.0, 256)
        self._img.setLookupTable(lut)

    def setData(self, data):
        self._img.setImage(data)


class TwodCubeViewer(object):
    def __init__(self, start_time=dt.datetime(2000, 1, 1), force_rename=True,
                 use_prev_settings=True, state_name=None):
        self._cubes = None
        self._displayed_cubes = OrderedDict()
        self._settings = OrderedDict()
        self._curr_time_index = 0
        self._curr_level_index = 0
        self._start_time = start_time
        self._force_rename = force_rename
        self._state_name = state_name
        self._use_prev_settings = use_prev_settings
        self.wins = {}

    def help(self, member_name=None):
        print_members = []
        max_len = 0
        for member in dir(self):
            if member[0] != '_':
                max_len = max(len(member), max_len)
                member_obj = getattr(self, member)
                if member == member_name:
                    print('{}:'.format(member))
                    print(member_obj.__doc__)

                print_members.append((member, member_obj))

        if not member_name:
            for member, member_obj in print_members:
                fmt = '{{0: <{}}}: {{1}}'.format(max_len)
                if member_obj.__doc__:
                    print(fmt.format(member, member_obj.__doc__.split('\n')[0]))
                else:
                    print(fmt.format(member, 'no docstring'))


    def load(self, filenames):
        filename = os.path.expanduser(filenames[0])
        print('Loading: {}'.format(filenames))
        self._file_dir = os.path.dirname(filename)
        self._filename = filename
        self._cubes = iris.load(filenames).concatenate()
        STASH.rename_unknown_cubes(self._cubes, self._force_rename)

        basename = os.path.basename(self._filename)
        self._settings_file = os.path.join(self._file_dir, '.tcv_settings.{}.pkl'.format(basename))
        if self._state_name:
            self.load_state(self._state_name, show=False)
        elif self._use_prev_settings:
            self._load_settings()

    def save_state(self, name):
        basename = os.path.basename(self._filename)
        state_file = os.path.join(self._file_dir, '.tcv_state.{}.{}.pkl'.format(name, basename))
        state = State(self._curr_time_index)
        settings = self._settings.copy()
        settings['state'] = state
        with open(state_file, 'w') as f:
            pickle.dump(settings, f)


    def load_state(self, name, show):
        basename = os.path.basename(self._filename)
        state_file = os.path.join(self._file_dir, '.tcv_state.{}.{}.pkl'.format(name, basename))
        with open(state_file, 'r') as f:
            settings = pickle.load(f)
            state = settings.pop('state')
            self._curr_time_index = state.curr_time_index
            self._settings = settings
        self._apply_settings()
        print('Current time index: {}'.format(self._curr_time_index))
        self.disp()
        if show:
            self.show()

    def list_state(self):
        for filename in glob(os.path.join(self._file_dir, '.tcv_state.*.pkl')):
            print(filename.split('.')[2])


    def _load_settings(self):
        if os.path.exists(self._settings_file):
            with open(self._settings_file, 'r') as f:
                self._settings = pickle.load(f)

        self._apply_settings()
        self.disp()

    def _apply_settings(self):
        for i, setting in self._settings.items():
            if setting.disp:
                self._add_disp_cube(i)

    def _save_settings(self):
        with open(self._settings_file, 'w') as f:
            pickle.dump(self._settings, f)

    def _add_disp_cube(self, index):
        cube = self._cubes[index]
        self._displayed_cubes[index] = cube
        self._check_displayed_cubes()

    def add_disp(self, index, ignore_first=False, map_index=None):
        cube = self._cubes[index]
        tmp_cube = cube.copy()  # Allow mem. release after use.
        setting = DispSetting(True, ignore_first, map_index, 
                              tmp_cube.data.max(), tmp_cube.data.min())
        del tmp_cube
        self._settings[index] = setting
        self._add_disp_cube(index)

        self._save_settings()
        self.disp()

    def rm_disp(self, index):
        del self._displayed_cubes[index]
        self._settings[index] = self._settings[index]._replace(disp=False)
        self._save_settings()
        self.disp()

    def _check_displayed_cubes(self):
        all_cube_length = None
        all_cube_height = None
        for i, cube in self._displayed_cubes.items():
            setting = self._settings[i]
            cube_length = cube.shape[0] - 1 if setting.ignore_first else cube.shape[0]
            if not all_cube_length:
                all_cube_length = cube_length
            else:
                if cube_length != all_cube_length:
                    print('Warning, cube length mismatch')

            if len(cube.shape) == 4:
                cube_height = cube.shape[1]
                if not all_cube_height:
                    all_cube_height = cube_height
                else:
                    if cube_height != all_cube_height:
                        print('Warning, cube height mismatch')

        self._all_cube_length = all_cube_length
        self._all_cube_height = all_cube_height
            
    def next(self):
        self.go(self._curr_time_index + 1)

    def prev(self):
        self.go(self._curr_time_index - 1)

    def go(self, time_index=None, level_index=None):
        'go to specified time_index'
        if time_index:
            if time_index < 0 or time_index >= self._all_cube_length:
                print('stopping')
                self.timer.stop()
            else:
                self._curr_time_index = time_index
        if level_index:
            if level_index < 0 or level_index >= self._all_cube_height:
                print('stopping')
                self.timer.stop()
            else:
                self._curr_level_index = level_index

        try:
            self.show()
        except:
            print('stopping')
            self.timer.stop()

    def up(self):
        self.go(level_index=self._curr_level_index + 1)

    def down(self):
        self.go(level_index=self._curr_level_index - 1)
    
    def update(self):
        self.go(self._curr_time_index + self.time_step, 
                self._curr_level_index + self.level_step)

    def stop(self):
        self.timer.stop()

    def play(self, length=None, timeout=1000, time_step=1, level_step=0):
        self.timeout = timeout
        self.time_step = time_step
        self.level_step = level_step
        self.show()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(timeout)

    def disp(self):
        for i, cube in enumerate(self._cubes):
            displayed = '*' if i in self._displayed_cubes else ' '
            setting = self._settings[i] if displayed == '*' else ''
            print('{0}: [{1}] {2:<36}, {3}, {4}'.format(i, displayed, cube.name(), 
                                                        cube.shape, setting))

    def show(self):
        for i, cube in self._displayed_cubes.items():
            if i not in self.wins:
                win = ImageWindow()
                win.show()
                self.wins[i] = win
            else:
                win = self.wins[i]

            setting = self._settings[i]
            if setting.map_index:
                curr_time_index = setting.map_index(self._curr_time_index)
            else:
                if setting.ignore_first:
                    curr_time_index = self._curr_time_index + 1
                else:
                    curr_time_index = self._curr_time_index

            time_hrs_since_19700101 = cube.coord('time').points[curr_time_index]
            time = dt.datetime(1970, 1, 1) + dt.timedelta(0, time_hrs_since_19700101 * 3600)
            elapsed_time = time - self._start_time

            cube_time = elapsed_time.days + elapsed_time.seconds/86400. 
            if len(cube.shape) == 3:
                title = '{0} - {1}: {2:.2f} days'.format(cube.name(),
                                                         curr_time_index, 
                                                         cube_time)
                win.setWindowTitle(title)
                win.setData(cube[curr_time_index].data)
            elif len(cube.shape) == 4:
                height = cube.coord('level_height').points[self._curr_level_index]
                title = '{0} - {1}: {2}: {3:.2f} days, {4:.2f} m'.format(cube.name(),
                                                                         curr_time_index,
                                                                         self._curr_level_index,
                                                                         cube_time, 
                                                                         height)
                win.setWindowTitle(title)
                win.setData(cube[curr_time_index, self._curr_level_index].data) 

