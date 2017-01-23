import os
from collections import namedtuple, OrderedDict
import datetime as dt
import pickle
from glob import glob
import warnings

import pylab as plt
import iris
import matplotlib.cbook
import dill # necessary to serialize lambdas.

import omnium

DispSetting = namedtuple('DispSetting', ['disp', 'ignore_first', 'map_index', 'vmax', 'vmin']) 
State = namedtuple('State', ['curr_time_index']) 

STASH = omnium.Stash()
# Fixes:
# iris/fileformats/cf.py:1140: IrisDeprecation: NetCDF default loading behaviour...
# warning message.
iris.FUTURE.netcdf_promote = True
# Suppresses matplotlib warning.
# http://stackoverflow.com/questions/24502500/python-matplotlib-getting-rid-of-matplotlib-mpl-warning
warnings.filterwarnings("ignore",category=matplotlib.cbook.mplDeprecation)


class TwodCubeViewer(object):
    def __init__(self, start_time=dt.datetime(2012, 9, 27, 21, 0), force_rename=True,
                 use_prev_settings=True, state_name=None):
        plt.ion()
        self._cubes = None
        self._displayed_cubes = OrderedDict()
        self._settings = OrderedDict()
        self._curr_time_index = 0
        self._start_time = start_time
        self._force_rename = force_rename
        self._state_name = state_name

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


    def load(self, filename):
        filename = os.path.expanduser(filename)
        print('Loading: {}'.format(filename))
        self._file_dir = os.path.dirname(filename)
        self._filename = filename
        self._cubes = iris.load(filename)
        STASH.rename_unknown_cubes(self._cubes, self._force_rename)

        basename = os.path.basename(self._filename)
        self._settings_file = os.path.join(self._file_dir, '.tcv_settings.{}.pkl'.format(basename))
        if self._state_name:
            self.load_state(self._state_name, show=False)
        else:
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

    def rm_disp(self, index):
        del self._displayed_cubes[index]
        self._settings[index] = self._settings[index]._replace(disp=False)
        self._save_settings()

    def _check_displayed_cubes(self):
        all_cube_length = None
        for i, cube in self._displayed_cubes.items():
            setting = self._settings[i]
            cube_length = cube.shape[0] - 1 if setting.ignore_first else cube.shape[0]
            if not all_cube_length:
                all_cube_length = cube_length
            else:
                if cube_length != all_cube_length:
                    print('Warning, cube length mismatch')
        self._all_cube_length = all_cube_length
            
    def next(self):
        self.go(self._curr_time_index + 1)

    def prev(self):
        self.go(self._curr_time_index - 1)

    def go(self, time_index):
        'go to specified time_index'
        self._curr_time_index = time_index
        self.show()

    def play(self, length=None, timeout=100, step=1):
        print('Ctrl-C to stop')
        while self._curr_time_index < self._all_cube_length and length != 0:
            try:
                if length:
                    length -= 1
                self.go(self._curr_time_index + step)
                plt.pause(timeout / 1000.)
            except KeyboardInterrupt:
                break

    def disp(self):
        for i, cube in enumerate(self._cubes):
            displayed = '*' if i in self._displayed_cubes else ' '
            setting = self._settings[i] if displayed == '*' else ''
            print('{0}: [{1}] {2:<36}, {3}, {4}'.format(i, displayed, cube.name(), cube.shape, setting))

    def show(self):
        for i, cube in self._displayed_cubes.items():
            setting = self._settings[i]
            if setting.map_index:
                curr_time_index = setting.map_index(self._curr_time_index)
            else:
                if setting.ignore_first:
                    curr_time_index = self._curr_time_index + 1
                else:
                    curr_time_index = self._curr_time_index

            plt.figure(cube.name())
            plt.clf()
            time_hrs_since_19700101 = cube.coord('time').points[curr_time_index]
            time = dt.datetime(1970, 1, 1) + dt.timedelta(0, time_hrs_since_19700101 * 3600)
            elapsed_time = time - self._start_time

            plt.title('{0}: {1:.2f} days'.format(curr_time_index, elapsed_time.days + elapsed_time.seconds/86400.) )
            plt.imshow(cube[curr_time_index].data, interpolation='nearest', origin='lower',
                       vmax=setting.vmax, vmin=setting.vmin)
            plt.pause(0.0001)
