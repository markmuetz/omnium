import abc
import datetime as dt
import os
from collections import OrderedDict
from logging import getLogger

import iris
from omnium.omnium_errors import OmniumError
from omnium.version import get_version

logger = getLogger('om.analyser')


class Analyser(object):
    __metaclass__ = abc.ABCMeta

    # One of these must be overridden by base class.
    single_file = False
    multi_file = False
    multi_expt = False

    @classmethod
    def gen_output_filename(cls, data_type, filename):
        split_filename = os.path.basename(filename).split('.')
        atmos = split_filename[0]
        analysis_name = cls.analysis_name
        multi_file = cls.multi_file
        runid = 0
        if data_type == 'datam':
            if len(split_filename) >= 3:
                try:
                    runid = int(split_filename[1])
                except:
                    runid = 0

                if multi_file:
                    # TODO: v hacky nipping off last 3 chars.
                    # self.output_filename = '{}.{}.nc'.format(runid[:-3], self.analysis_name)
                    output_filename = '{}.{}.nc'.format(atmos, analysis_name)
                else:
                    output_filename = '{}.{:03}.{}.nc'.format(atmos, runid, analysis_name)
            elif len(split_filename) <= 2:
                logger.debug('analysing dump')
                # It's a dump. Should have a better way of telling though.
                if multi_file:
                    # TODO: hacky - nip off final 024, e.g. atmosa_da024 -> atmosa_da.
                    dump_without_time_hours = split_filename[0][:-3]
                    output_filename = '{}.{}.nc'.format(dump_without_time_hours,
                                                        analysis_name)
                else:
                    output_filename = '{}.{}.nc'.format(split_filename[0], analysis_name)
        elif data_type == 'dataw':
            output_filename = '{}.{}.nc'.format(atmos, analysis_name)
        return runid, output_filename

    def __init__(self, suite, task, results_dir, expt_group=None):
        assert sum([self.single_file, self.multi_file, self.multi_expt]) == 1
        assert self.analysis_name
        self.suite = suite
        self.task = task
        self.results_dir = results_dir
        self.expt_group = expt_group
        if self.multi_expt:
            self.expt = None
            self.expts = task.expts
        else:
            self.expt = task.expt
            self.expts = None

        if self.multi_file:
            self.filenames = task.filenames
            self.filename = None
        else:
            if self.multi_expt:
                self.filenames = task.filenames
                self.filename = None
            else:
                # assert len(task.filenames) == 1
                self.filename = task.filenames[0]
                split_filename = self.filename.split()
                try:
                    self.runid = int(split_filename[1])
                except:
                    self.runid = None

        self.output_filename = task.output_filenames[0]

        logger.debug('single_file: {}'.format(self.single_file))
        logger.debug('multi_file: {}'.format(self.multi_file))
        logger.debug('multi_expt: {}'.format(self.multi_expt))

        logger.debug('output_filename: {}'.format(self.output_filename))
        self.results = OrderedDict()
        self.force = False
        # N.B. there is only one results_dir, even for multi_expt
        self.logname = os.path.join(self.results_dir, self.output_filename + '.analysed')
        if self.suite and self.suite.check_filename_missing(self.logname):
            os.remove(self.logname)

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
        self.delete = self._config.getboolean('delete', False)
        self.min_runid = self._config.getint('min_runid', 0)
        self.max_runid = self._config.getint('max_runid', int(1e10))

    def already_analysed(self):
        return os.path.exists(self.logname) and not self.suite.check_filename_missing(self.logname)

    def append_log(self, message):
        logger.debug('{}: {}'.format(self.analysis_name, message))
        with open(self.logname, 'a') as f:
            f.write('{}: {}\n'.format(dt.datetime.now(), message))

    def load(self):
        self.append_log('Loading')
        if self.multi_file:
            for filename in self.filenames:
                self.suite.abort_if_missing(filename)
            self.cubes = iris.load(self.filenames)
        else:
            if self.multi_expt:
                self.expt_cubes = OrderedDict()
                for expt, filename in zip(self.expts, self.filenames):
                    logger.debug('loading fn:{}'.format(filename))
                    self.suite.abort_if_missing(filename)
                    self.expt_cubes[expt] = iris.load(filename)
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
        self.append_log('Analysing')
        if interactive:
            logger.info('Running interactively')
            import ipdb
            ipdb.runcall(self.run_analysis)
        else:
            self.run_analysis()
        self.append_log('Analysed')

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
                hash_str = ':'.join([h.decode() for h in suite.analysis_hash])
                cube.attributes['omnium_analysers_git_hash'] = hash_str
                cube.attributes['omnium_analysers_git_status'] = ':'.join(suite.analysis_status)

            cube.attributes['omnium_process'] = self.analysis_name

        cubelist = iris.cube.CubeList(list(self.results.values()))
        if not len(cubelist):
            logger.warning('No results to save')
        else:
            logger.debug('saving to {}'.format(cubelist_filename))
            # logger.debug('Not using zlib')
            # TODO: Make this a setting somewhere.
            # Use default compression: complevel 4.
            if os.path.exists(cubelist_filename) and os.path.islink(cubelist_filename):
                logger.debug('Removing symlink')
                os.remove(cubelist_filename)
            iris.save(cubelist, cubelist_filename, zlib=True)
            # iris.save(cubelist, cubelist_filename)

        self.append_log('Saved')
        open(cubelist_filename + '.done', 'a').close()

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

    def save_text(self, name, text):
        filepath = self.figpath(name)
        logger.debug('Saving text to: {}'.format(filepath))
        for line in text.split('\n'):
            logger.debug(line)

        filepath = self.figpath(name)
        with open(filepath, 'w') as f:
            f.write(text)

    def figpath(self, name):
        figdir = os.path.join(self.results_dir, 'figs')
        if self.expt_group and self.multi_expt:
            figdir = os.path.join(figdir, self.expt_group)

        if not os.path.exists(figdir):
            os.makedirs(figdir)

        if self.multi_expt:
            filename = 'atmos.{}.{}'.format(self.analysis_name, name)
        elif self.multi_file:
            filename = 'atmos.{}.{}'.format(self.analysis_name, name)
        else:
            filename = 'atmos.{}.{}.{}'.format(self.runid, self.analysis_name, name)
        _figpath = os.path.join(figdir, filename)
        self.append_log('Saving fig to: {}'.format(_figpath))
        return _figpath

    @abc.abstractmethod
    def run_analysis(self):
        return
