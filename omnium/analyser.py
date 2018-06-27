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
    uses_runid = False
    min_runid = 0
    max_runid = int(1e10)

    settings = None

    def __init__(self, suite, task):
        assert sum([self.single_file, self.multi_file, self.multi_expt]) == 1
        assert self.analysis_name
        if self.settings:
            logger.debug('using settings: {}', self.settings.get_hash())
        self.suite = suite
        self.task = task

        logger.debug('single_file: {}', self.single_file)
        logger.debug('multi_file: {}', self.multi_file)
        logger.debug('multi_expt: {}', self.multi_expt)

        logger.debug('output_filenames: {}', self.output_filenames)
        self.cube_results = OrderedDict()
        self.force = False
        # N.B. there is only one results_dir, even for multi_expt
        self.logname = os.path.join(self.task.output_filenames[0] + '.analysed')
        if self.suite and self.suite.check_filename_missing(self.logname):
            os.remove(self.logname)

        # Need to make sure results dir exists before first call to self.append_log.
        for results_dir in [os.path.dirname(f) for f in self.task.output_filenames]:
            if not os.path.exists(results_dir):
                logger.debug('creating results_dir: {}', results_dir)
                os.makedirs(results_dir)

    @abc.abstractmethod
    def load(self):
        return

    @abc.abstractmethod
    def run(self):
        return

    @abc.abstractmethod
    def save(self, state=None, suite=None):
        return

    def analysis_load(self):
        self.append_log('Loading')
        self.load()
        self.append_log('Loaded')

    def analysis_run(self):
        self.append_log('Analysing')
        self.run()
        self.append_log('Analysed')

    def analysis_save(self, state=None, suite=None):
        self.append_log('Saving')
        self.save(state, suite)
        self.append_log('Saved')

    def analysis_display(self):
        if hasattr(self, 'display_results'):
            self.append_log('Displaying results')
            self.display_results()
            self.append_log('Displayed')
        else:
            self.append_log('No results display')

    def analysis_done(self):
        missing_filenames = []
        for output_filename in self.task.output_filenames:
            if not os.path.exists(output_filename):
                missing_filenames.append(output_filename)
        if missing_filenames:
            raise OmniumError('Some output filenames not produced: {}'.format(missing_filenames))
        for output_filename in self.task.output_filenames:
            open(output_filename + '.done', 'a').close()

    def already_analysed(self):
        return os.path.exists(self.logname) and not self.suite.check_filename_missing(self.logname)

    def append_log(self, message):
        logger.debug('{}: {}', self.analysis_name, message)
        with open(self.logname, 'a') as f:
            f.write('{}: {}\n'.format(dt.datetime.now(), message))

    def load_cubes(self):
        self.append_log('Loading')

        if self.multi_file:
            filenames = self.task.filenames
            for filename in filenames:
                self.suite.abort_if_missing(filename)
            cubes = iris.load(filenames)
            self.cubes = iris.cube.CubeList.concatenate(cubes)

        else:
            if self.multi_expt:
                filenames = self.task.filenames
                self.expt_cubes = OrderedDict()
                for expt, filename in zip(self.expts, filenames):
                    logger.debug('loading fn:{}', filename)
                    self.suite.abort_if_missing(filename)
                    self.expt_cubes[expt] = iris.load(filename)
            else:
                # assert len(task.filenames) == 1
                filename = self.task.filenames[0]
                logger.debug('loading {}', filename)
                self.suite.abort_if_missing(filename)
                self.cubes = iris.load(filename)

        self.append_log('Loaded')

    def save_text(self, name, text):
        filepath = self.display_path(name)
        logger.debug('Saving text to: {}', filepath)
        for line in text.split('\n'):
            logger.debug(line)

        with open(filepath, 'w') as f:
            f.write(text)

    def save_cube_results(self, cubelist_filename, state=None, suite=None):
        self.append_log('Saving cubelist'.format(cubelist_filename))

        for cube_id, cube in self.cube_results.items():
            logger.debug('saving cube: {}', cube.name())
            logger.debug('omnium_cube_id: {}', cube_id)
            logger.debug('cube shape: {}', cube.shape)

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

        cubelist = iris.cube.CubeList(list(self.cube_results.values()))
        if not len(cubelist):
            logger.warning('No cube_results to save')
        else:
            logger.debug('saving to {}', cubelist_filename)
            # logger.debug('Not using zlib')
            # TODO: Make this a setting somewhere.
            # Use default compression: complevel 4.
            if os.path.exists(cubelist_filename) and os.path.islink(cubelist_filename):
                logger.debug('Removing symlink')
                os.remove(cubelist_filename)
            iris.save(cubelist, cubelist_filename, zlib=True)
            # iris.save(cubelist, cubelist_filename)

        self.append_log('Saved cubelist'.format(cubelist_filename))

    def display_path(self, name):
        output_dir = os.path.dirname(self.task.output_filenames[0])
        return os.path.join(self.suite.suite_dir, output_dir, name)
