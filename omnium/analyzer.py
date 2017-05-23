import os
import datetime as dt
from glob import glob
from collections import OrderedDict
import abc
from logging import getLogger

import iris

from omnium.omnium_errors import OmniumError
from omnium.version import get_version

logger = getLogger('omnium')


class Analyzer(object):
    __metaclass__ = abc.ABCMeta

    @staticmethod
    def get_files(data_dir, filename):
        return sorted(glob(os.path.join(data_dir, filename)))

    def __init__(self, data_type, data_dir, results_dir, 
                 filenames, expts, multi_file=False, multi_expt=False):

        if multi_file and multi_expt:
            raise OmniumError('Only one of multi_file, multi_expt can be True')
        self.data_type = data_type
        self.data_dir = data_dir
        self.results_dir = results_dir
        self.multi_file = multi_file
        self.multi_expt = multi_expt
        if multi_expt:
            self.expt = None
            self.expts = expts
        else:
            assert len(expts) == 1
            self.expt = expts[0]
            self.expts = None

        if self.multi_file:
            self.filenames = filenames
            self.filename = None
            filename = self.filenames[0]
        else:
            assert len(filenames) == 1
            filename = filenames[0]
            if self.multi_expt:
                self.expt_filename = OrderedDict()
                for expt in self.expts:
                    self.expt_filename[expt] = os.path.join(self.data_dir[expt], filename)
                filename = self.expt_filename.values()[0]
            else:
                self.filename = os.path.join(self.data_dir[self.expt], filename)
            self.filenames = None

        logger.debug('data_type: {}'.format(data_type))
        logger.debug('multi_file: {}'.format(self.multi_file))
        logger.debug('multi_expt: {}'.format(self.multi_expt))

        split_filename = filename.split('.')
        runid = split_filename[0]

        logger.debug('split_filename: {}'.format(split_filename))
        logger.debug('filename: {}'.format(filename))
        if data_type == 'datam':
            if len(split_filename) >= 3:
                time_hours = split_filename[1]
                instream = split_filename[2]
                if self.multi_file:
                    # TODO: v hacky nipping off last 3 chars.
                    self.output_filename = '{}.{}.nc'.format(runid[:-3], self.analysis_name)
                else:
                    self.output_filename = '{}.{}.{}.nc'.format(runid,
                                                                time_hours,
                                                                self.analysis_name)
            elif len(split_filename) <= 2:
                logger.debug('Analyzing dump')
                # It's a dump. Should have a better way of telling though.
                if self.multi_file:
                    # TODO: hacky - nip off final 024, e.g. atmosa_da024 -> atmosa_da.
                    dump_without_time_hours = split_filename[0][:-3]
                    self.output_filename = '{}.{}.nc'.format(dump_without_time_hours,
                                                             self.analysis_name)
                else:
                    self.output_filename = '{}.{}.nc'.format(split_filename[0], self.analysis_name)
        elif data_type == 'dataw':
            instream = split_filename[1]
            self.output_filename = '{}.{}.nc'.format(runid, self.analysis_name)

        logger.debug('output_filename: {}'.format(self.output_filename))
        self.results = OrderedDict()
        self.force = False
        # N.B. there is only one results_dir, even for multi_expt
        self.logname = os.path.join(self.results_dir, self.output_filename + '.analyzed')

    def set_config(self, config):
        self._config = config
        if 'force' in self._config:
            self.force = self._config['force'] == 'True'

    def already_analyzed(self):
        return os.path.exists(self.logname)

    def append_log(self, message):
        logger.debug('{}: {}'.format(self.analysis_name, message))
        with open(self.logname, 'a') as f:
            f.write('{}: {}\n'.format(dt.datetime.now(), message))

    def load(self):
        self.append_log('Loading')
        if self.multi_file:
            logger.debug('Loading {}'.format(self.filenames))
            self.cubes = iris.load(self.filenames)
        else:
            if self.multi_expt:
                self.expt_cubes = OrderedDict()
                for expt in self.expts:
                    self.expt_cubes[expt] = iris.load(self.expt_filename[expt])
            else:
                self.cubes = iris.load(self.filename)

        self.append_log('Loaded')

    def run(self):
        self.append_log('Analyzing')
        self.run_analysis()
        self.append_log('Analyzed')

    def save(self):
        self.append_log('Saving')
        if not os.path.exists(self.results_dir):
            logger.debug('Creating results_dir: {}'.format(self.results_dir))
            os.makedirs(self.results_dir)

        cubelist_filename = os.path.join(self.results_dir, self.output_filename)
        for cube_id, cube in self.results.items():
            logger.debug('Saving cube: {}'.format(cube.name()))
            logger.debug('omnium_cube_id: {}'.format(cube_id))
            cube.attributes['omnium_vn'] = get_version('long')
            cube.attributes['omnium_cube_id'] = cube_id
        cubelist = iris.cube.CubeList(self.results.values())
        if not len(cubelist):
            logger.warn('No results to save')
        else:
            iris.save(cubelist, cubelist_filename)

        self.save_analysis()
        self.append_log('Saved')

    def save_analysis(self):
        pass

    @abc.abstractmethod
    def run_analysis(self):
        return
