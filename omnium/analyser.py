import abc
import datetime as dt
import os
from collections import OrderedDict
from logging import getLogger
import re

import iris
from omnium.omnium_errors import OmniumError
from omnium.version import get_version

logger = getLogger('om.analyser')


class Analyser(abc.ABC):
    analysis_name = None
    # One of these must be overridden by base class.
    single_file = False
    multi_file = False
    multi_expt = False

    input_dir = None

    # One of these must be overridden by base class.
    input_filename_glob = None
    input_filename = None
    input_filenames = None

    output_dir = None
    output_filenames = None

    uses_runid = False
    min_runid = 0
    max_runid = int(1e10)
    runid_pattern = None

    force = False
    delete = False

    @abc.abstractmethod
    def load(self):
        return

    @abc.abstractmethod
    def run(self):
        return

    @abc.abstractmethod
    def save(self, state, suite):
        return

    @classmethod
    def get_runid(cls, filename):
        assert cls.uses_runid and cls.runid_pattern
        filename = os.path.basename(filename)
        match = re.match(cls.runid_pattern, filename)
        if match:
            return int(match['runid'])
        else:
            raise OmniumError('Could not find runid in {} using {}', filename, cls.runid_pattern)

    def __init__(self, suite, task, settings):
        assert sum([self.single_file, self.multi_file, self.multi_expt]) == 1
        assert self.analysis_name
        if self.uses_runid:
            assert self.runid_pattern
        assert self.input_dir
        assert sum([self.input_filename_glob is not None,
                    self.input_filename is not None,
                    self.input_filenames is not None]) == 1
        assert self.output_dir
        assert self.output_filenames

        self.settings = settings
        if self.settings:
            logger.debug('using settings: {}', self.settings.get_hash())
        self.suite = suite
        self.task = task
        self.output_filename = task.output_filenames[0]

        logger.debug('single_file: {}', self.single_file)
        logger.debug('multi_file: {}', self.multi_file)
        logger.debug('multi_expt: {}', self.multi_expt)

        logger.debug('output_filename: {}', self.output_filename)
        self.results = OrderedDict()
        # N.B. there is only one output_dir, even for multi_expt
        logdir = os.path.dirname(self.output_filename)
        self.logname = os.path.join(logdir, self.output_filename + '.log')
        if self.suite and self.suite.check_filename_missing(self.logname):
            os.remove(self.logname)

        # Need to make sure output dirs exists before first call to self.append_log.
        for output_dir in [os.path.dirname(fn) for fn in self.task.output_filenames]:
            if not os.path.exists(output_dir):
                logger.debug('creating output_dir: {}', output_dir)
                os.makedirs(output_dir)

    def already_started_analysing(self):
        missing = self.suite.check_filename_missing(self.logname)
        return os.path.exists(self.logname) or missing

    def already_analysed(self):
        missing_filenames = []
        for output_filename in self.task.output_filenames:
            done_filename = output_filename + '.done'
            not_missing = not self.suite.check_filename_missing(done_filename)
            if (not os.path.exists(done_filename) and not_missing):
                missing_filenames.append(output_filename)
        return missing_filenames == []

    def append_log(self, message):
        logger.debug('{}: {}', self.analysis_name, message)

    def load_cubes(self):
        self.append_log('Loading cubes')

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
                for expt, filename in zip(self.task.expts, filenames):
                    logger.debug('loading fn:{}', filename)
                    self.suite.abort_if_missing(filename)
                    self.expt_cubes[expt] = iris.load(filename)
            else:
                filename = self.task.filenames[0]
                logger.debug('loading {}', filename)
                self.suite.abort_if_missing(filename)
                self.cubes = iris.load(filename)

        self.append_log('Loaded cubes')

    def save_results_cubes(self, state=None, suite=None):
        self.append_log('Saving cubes')

        cubelist_filename = self.output_filename
        for cube_id, cube in self.results.items():
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

        cubelist = iris.cube.CubeList(list(self.results.values()))
        if not len(cubelist):
            logger.warning('No results to save')
        else:
            logger.debug('saving to {}', cubelist_filename)
            save_kwargs = {'zlib': True}
            if self.settings.has_item('zlib'):
                save_kwargs['zlib'] = self.settings.zlib
            if self.settings.has_item('complevel'):
                save_kwargs['complevel'] = self.settings.complevel
            logger.debug('Using save_kwargs: {}', str(save_kwargs))

            if os.path.exists(cubelist_filename) and os.path.islink(cubelist_filename):
                logger.debug('Removing symlink')
                os.remove(cubelist_filename)
            iris.save(cubelist, cubelist_filename, **save_kwargs)

        self.append_log('Saved cubes')

    def analysis_load(self):
        self.append_log('Loading')
        self.load()
        self.append_log('Loaded')

    def analysis_run(self):
        self.append_log('Analysing')
        self.run()
        self.append_log('Analysed')

    def analysis_save(self, state, suite):
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
            logger.info('Created filename: {}', output_filename)
            open(output_filename + '.done', 'a').close()
        self.append_log('Done')

    def save_text(self, name, text):
        file_path = self.file_path(name)
        logger.debug('Saving text to: {}', file_path)
        for line in text.split('\n'):
            logger.debug(line)

        with open(file_path, 'w') as f:
            f.write(text)

    def file_path(self, name):
        file_path_dir = os.path.dirname(self.output_filename)

        if not os.path.exists(file_path_dir):
            logger.debug('making dir: {}', file_path_dir)
            os.makedirs(file_path_dir)

        filename = os.path.join(file_path_dir, name)
        logger.debug('using filename: {}', filename)
        return filename
