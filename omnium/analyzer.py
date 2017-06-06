import os
import datetime as dt
from glob import glob
from collections import OrderedDict
import abc
from logging import getLogger

import iris

from omnium.omnium_errors import OmniumError
from omnium.version import get_version

logger = getLogger('om.analyzer')


class Analyzer(object):
    __metaclass__ = abc.ABCMeta

    multi_file = False
    multi_expt = False

    @staticmethod
    def get_files(data_dir, filename):
        return sorted(glob(os.path.join(data_dir, filename)))

    def __init__(self, suite, data_type, data_dir, results_dir,
                 filenames, expts, expt_group=None):

        if self.multi_file and self.multi_expt:
            raise OmniumError('Only one of multi_file, multi_expt can be True')
        self.suite = suite
        self.data_type = data_type
        self.data_dir = data_dir
        self.results_dir = results_dir
        self.expt_group = expt_group
        if self.multi_expt:
            self.expt = None
            self.expts = expts
        else:
            assert len(expts) == 1
            self.expt = expts[0]
            self.expts = None

        if self.multi_file:
            self.filenames = filenames
            self.filename = None
            filename = os.path.basename(self.filenames[0])
        else:
            assert len(filenames) == 1
            filename = os.path.basename(filenames[0])
            if self.multi_expt:
                self.expt_filename = OrderedDict()
                for expt in self.expts:
                    self.expt_filename[expt] = os.path.join(self.data_dir[expt], filename)
                filename = os.path.basename(self.expt_filename.values()[0])
            else:
                self.filename = os.path.join(self.data_dir[self.expt], filename)
            self.filenames = None

        logger.debug('data_type: {}'.format(data_type))
        logger.debug('multi_file: {}'.format(self.multi_file))
        logger.debug('multi_expt: {}'.format(self.multi_expt))

        split_filename = filename.split('.')
        runid = split_filename[0]

        logger.debug('filename: {}'.format(filename))
        logger.debug('split_filename: {}'.format(split_filename))
        if data_type == 'datam':
            if len(split_filename) >= 3:
                time_hours = split_filename[1]
                instream = split_filename[2]
                if self.multi_file:
                    # TODO: v hacky nipping off last 3 chars.
                    # self.output_filename = '{}.{}.nc'.format(runid[:-3], self.analysis_name)
                    self.output_filename = '{}.{}.nc'.format(runid, self.analysis_name)
                else:
                    self.output_filename = '{}.{}.{}.nc'.format(runid,
                                                                time_hours,
                                                                self.analysis_name)
            elif len(split_filename) <= 2:
                logger.debug('analyzing dump')
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

        # Need to make sure results dir exists before first call to self.append_log.
        if not os.path.exists(self.results_dir):
            logger.debug('creating results_dir: {}'.format(self.results_dir))
            os.makedirs(self.results_dir)

    def set_config(self, config):
        logger.debug(config)
        for item in config.items():
            logger.debug(item)
        self._config = config
        self.force = self._config.getboolean('force', False)

    def already_analyzed(self):
        return os.path.exists(self.logname) and not self.suite.check_filename_missing(self.logname)

    def append_log(self, message):
        logger.debug('{}: {}'.format(self.analysis_name, message))
        with open(self.logname, 'a') as f:
            f.write('{}: {}\n'.format(dt.datetime.now(), message))

    def load(self):
        self.append_log('Loading')
        if self.multi_file:
            logger.debug('loading {}'.format(self.filenames))
            for filename in self.filenames:
                self.suite.abort_if_missing(filename)
            self.cubes = iris.load(self.filenames)
        else:
            if self.multi_expt:
                self.expt_cubes = OrderedDict()
                for expt in self.expts:
                    logger.debug('loading expt:{} fn:{}'.format(expt, self.expt_filename[expt]))
                    self.suite.abort_if_missing(self.expt_filename[expt])
                    self.expt_cubes[expt] = iris.load(self.expt_filename[expt])
            else:
                logger.debug('loading {}'.format(self.filename))
                self.suite.abort_if_missing(self.filename)
                self.cubes = iris.load(self.filename)

        self.append_log('Loaded')

    def load_results(self):
        cubelist_filename = os.path.join(self.results_dir, self.output_filename)
        if not os.path.exists(cubelist_filename):
            raise OmniumError('Results file does not exist')
        self.append_log('Loading results: {}'.format(cubelist_filename))
        cubes = iris.load(cubelist_filename)
        for cube in cubes:
            omnium_cube_id = cube.attributes['omnium_cube_id']
            self.results[omnium_cube_id] = cube
        self.append_log('Loaded results')

    def run(self, interactive=False):
        self.append_log('Analyzing')
        if interactive:
            logger.info('Running interactively')
            import ipdb
            ipdb.runcall(self.run_analysis)
        else:
            self.run_analysis()
        self.append_log('Analyzed')

    def save(self, state=None, suite=None):
        self.append_log('Saving')

        cubelist_filename = os.path.join(self.results_dir, self.output_filename)
        for cube_id, cube in self.results.items():
            logger.debug('saving cube: {}'.format(cube.name()))
            logger.debug('omnium_cube_id: {}'.format(cube_id))
            logger.debug('cube shape: {}'.format(cube.shape))

            cube.attributes['omnium_vn'] = get_version('long')
            cube.attributes['omnium_cube_id'] = cube_id

            if state:
                cube.attributes['omnium_git_hash'] = state.git_hash
                cube.attributes['omnium_git_status'] = state.git_status
            if suite:
                cube.attributes['omnium_analyzers_git_hash'] = ':'.join(suite.analysis_hash)
                cube.attributes['omnium_analyzers_git_status'] = ':'.join(suite.analysis_status)

            cube.attributes['omnium_process'] = self.analysis_name

        cubelist = iris.cube.CubeList(self.results.values())
        if not len(cubelist):
            logger.warn('No results to save')
        else:
            logger.debug('saving to {}'.format(cubelist_filename))
            # logger.debug('Not using zlib')
            # TODO: Make this a setting somewhere.
            # Use default compression: complevel 4.
            iris.save(cubelist, cubelist_filename, zlib=True)
            # iris.save(cubelist, cubelist_filename)

        self.append_log('Saved')

    def display(self, interactive=False):
        if hasattr(self, 'display_results'):
            self.append_log('Displaying results')
            if interactive:
                logger.info('Running interactively')
                import ipdb
                ipdb.runcall(self.display_results)
            else:
                self.display_results()
            self.append_log('Displayed')
        else:
            self.append_log('No results display')

    def figpath(self, name):
        figdir = os.path.join(self.results_dir, 'figs')
        if self.expt_group and self.multi_expt:
            figdir = os.path.join(figdir, self.expt_group)

        if not os.path.exists(figdir):
            os.makedirs(figdir)

        _figpath = os.path.join(figdir, self.output_filename + name)
        self.append_log('Saving fig to: {}'.format(_figpath))
        return _figpath

    @abc.abstractmethod
    def run_analysis(self):
        return
