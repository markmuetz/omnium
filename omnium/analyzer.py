import os
import datetime as dt
from glob import glob
from collections import OrderedDict
import abc
from logging import getLogger

import iris

logger = getLogger('omnium')


class Analyzer(object):
    __metaclass__ = abc.ABCMeta

    @staticmethod
    def get_files(data_dir, filename):
        return sorted(glob(os.path.join(data_dir, filename)))

    def __init__(self, suite, expt, data_type, data_dir, results_dir, filename):
        logger.debug(filename)
        self.suite = suite
        self.expt = expt
        self.data_type = data_type
        self.data_dir = data_dir
        self.results_dir = results_dir
        if filename:
            self.filename = os.path.join(self.data_dir, filename)
        else:
            self.filename = filename

        self.name = '{}_{}_{}_{}'.format(filename, suite, expt, self.analysis_name)
        logger.debug(self.name)

        split_filename = filename.split('.')
        runid = split_filename[0]

        if data_type == 'datam':
            if len(split_filename) >= 3:
                time_hours = split_filename[1]
                instream = split_filename[2]
                self.output_filename = '{}.{}.{}.nc'.format(runid, time_hours, self.analysis_name)
            elif len(split_filename) == 1:
                # It's a dump. Should have a better way of telling though.
                self.output_filename = '{}.{}.nc'.format(filename, self.analysis_name)
        elif data_type == 'dataw':
            instream = split_filename[1]
            self.output_filename = '{}.{}.nc'.format(runid, self.analysis_name)

        self.results = OrderedDict()
        self.force = False
        self.logname = self.output_filename + '.analyzed'

    def set_config(self, config):
        self._config = config
        if 'force' in self._config:
            self.force = self._config['force'] == 'True'

    def already_analyzed(self):
        return os.path.exists(self.logname)

    def append_log(self, message):
        with open(self.logname, 'a') as f:
            f.write('{}: {}\n'.format(dt.datetime.now(), message))

    def load(self):
        self.append_log('Loading')
        self.cubes = iris.load(self.filename)
        self.append_log('Loaded')

    def run(self):
        self.append_log('Analyzing')
        self.run_analysis()
        self.append_log('Analyzed')

    def save(self):
        self.append_log('Saving')
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

        cubelist_filename = os.path.join(self.results_dir, self.output_filename)
        cubelist = iris.cube.CubeList(self.results.values())

        iris.save(cubelist, cubelist_filename)

        self.save_analysis()
        self.append_log('Saved')

    def save_analysis(self):
        pass

    @abc.abstractmethod
    def run_analysis(self):
        return
