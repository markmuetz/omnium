import os
import datetime as dt
from glob import glob
from collections import OrderedDict
import abc
from logging import getLogger

import iris

from omnium.omnium_errors import OmniumError

logger = getLogger('omnium')


class Analyzer(object):
    __metaclass__ = abc.ABCMeta

    @staticmethod
    def get_files(data_dir, filename):
        return sorted(glob(os.path.join(data_dir, filename)))

    def __init__(self, suite, data_type, data_dir,
                 results_dir, expt, filename=None, filenames=None):
        if (filename and filenames) or (not filename and not filenames):
            raise OmniumError('Analyzer should be called with one of filename and filenames')
        self.suite = suite
        self.expt = expt
        self.data_type = data_type
        self.data_dir = data_dir
        self.results_dir = results_dir
        if filename:
            self.filename = os.path.join(self.data_dir, filename)
            self.filenames = None
            self.multi_file = False
        else:
            self.filenames = [os.path.join(self.data_dir, fn) for fn in filenames]
            self.filename = None
            self.multi_file = True
            filename = self.filenames[0]

        logger.debug('data_type: {}'.format(data_type))
        logger.debug('multi_file: {}'.format(self.multi_file))

        split_filename = filename.split('.')
        runid = split_filename[0]

        logger.debug('filename: {}'.format(filename))
        if data_type == 'datam':
            if len(split_filename) >= 3:
                time_hours = split_filename[1]
                instream = split_filename[2]
                if self.multi_file:
                    self.output_filename = '{}.{}.nc'.format(runid, self.analysis_name)
                else:
                    self.output_filename = '{}.{}.{}.nc'.format(runid,
                                                                time_hours,
                                                                self.analysis_name)
            elif len(split_filename) <= 2:
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
        self.logname = os.path.join(self.results_dir, self.output_filename + '.analyzed')

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
        if self.multi_file:
            logger.debug('Loading {}'.format(self.filenames))
            self.cubes = iris.load(self.filenames)
        else:
            logger.debug('Loading {}'.format(self.filename))
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
