import os
import sys
from glob import glob
from collections import OrderedDict
from logging import getLogger

from omnium.converters import CONVERTERS
from omnium.omnium_errors import OmniumError
from omnium.state import State

logger = getLogger('om.run_ctrl')


class RunControl(object):
    def __init__(self, suite, run_type, expts, production=False,
                 force=False, display_only=False, interactive=False):
        self.suite = suite
        self.production = production

        self.run_type = run_type
        if self.run_type == 'suite':
            self.expts = expts
        else:
            assert len(expts) == 1
            self.expts = expts

        self.force = force
        self.display_only = display_only
        self.interactive = interactive

        logger.warn('Disabling Python warnings')
        import warnings
        warnings.filterwarnings("ignore")
        self.state = State()

        self.setup()
        self.check_setup()

    def __repr__(self):
        return 'RunControl({}, "{}", {})'.format(repr(self.suite), self.run_type, self.expts)

    def setup(self):
        suite = self.suite

        if self.production:
            logger.debug('running in production mode')
            if self.state.git_status != 'clean':
                raise OmniumError('omnium is not clean, not running')
            for status in suite.analysis_status:
                if status != 'clean':
                    raise OmniumError('omnium analysis not all clean clean, not running')

        work_dir = os.path.join(self.suite.suite_dir, 'work')
        initial_cycle_point_dir = sorted(glob(os.path.join(work_dir, '*')))[0]
        initial_cycle_point = os.path.basename(initial_cycle_point_dir)
        suite_dir = suite.suite_dir

        self.atmos_datam_dir = {}
        self.atmos_dataw_dir = {}

        for expt in self.expts:
            self.atmos_datam_dir[expt] = os.path.join(suite_dir, 'share/data/history', expt)
            self.atmos_dataw_dir[expt] = os.path.join(suite_dir, 'work',
                                                      initial_cycle_point, expt + '_atmos')

        config = self.suite.app_config
        run_type = self.run_type

        settings_sec = 'settings_{}'.format(run_type)

        self.settings = config[settings_sec]

    def check_setup(self):
        for expt in self.expts:
            data_dir = self.atmos_datam_dir[expt]
            if not os.path.exists(data_dir):
                logger.warn('Dir does not exist: {}'.format(data_dir))
            data_dir = self.atmos_dataw_dir[expt]
            if not os.path.exists(data_dir):
                logger.warn('Dir does not exist: {}'.format(data_dir))

    def print_setup(self):
        for attr in ['run_type', 'expts', 'atmos_datam_dir', 'atmos_dataw_dir']:
            print('{}: {}'.format(attr, getattr(self, attr)))

    def run(self):
        self.gen_analysis_workflow()
        self.run_all()

    def convert_all(self, converter_name, filename_globs, overwrite, delete):
        for expt in self.expts:
            if self.run_type == 'cycle':
                data_dir = self.atmos_datam_dir[expt]
            elif self.run_type == 'expt':
                data_dir = self.atmos_dataw_dir[expt]

            filenames = []
            logger.info('Converting files like:')
            for filename_glob in filename_globs:
                logger.info('  ' + filename_glob)
                for filename in sorted(glob(os.path.join(data_dir, filename_glob))):
                    # Make sure that UM has finished writing file.
                    if os.path.exists(filename + '.done'):
                        logger.debug('  Adding: {}'.format(filename))
                        filenames.append(filename)
                    else:
                        logger.warn('  Not finished: {}'.format(filename))

            converter = CONVERTERS[converter_name](overwrite, delete)
            filenames_for_conversion = []
            for filename in filenames:
                # Check that file is not being converted by another process.
                if os.path.exists(filename + '.converting'):
                    logger.warn('  Already being converted: {}'.format(filename))
                else:
                    with open(filename + '.converting', 'w') as f:
                        f.write('Converting with {}\n'.format(converter_name))
                    filenames_for_conversion.append(filename)

            if not filenames:
                logger.warn('No files to convert')

            for filename in filenames_for_conversion:
                try:
                    converter.convert(filename)
                    # N.B. if converter fails, there will be a left over .converting file.
                    # This is intentional: I want to see if this has failed.
                    os.remove(filename + '.converting')
                except OmniumError as oe:
                    logger.error('Could not convert {}'.format(filename))
                    logger.error(oe)

            if not filenames_for_conversion:
                logger.warn('No files not already being converted to convert')

    def run_convert(self):
        convert = self.settings.getboolean('convert', False)
        if convert:
            converter_name = self.settings.get('converter', 'ff2nc')
            overwrite = self.settings.getboolean('overwrite', False)
            delete = self.settings.getboolean('delete', False)
            filename_globs = self.settings['filenames'].split(',')
            self.convert_all(converter_name, filename_globs, overwrite, delete)

    def gen_analysis_workflow(self):
        self.analysis_workflow = OrderedDict()

        runcontrol_sec = 'runcontrol_{}'.format(run_type)
        if runcontrol_sec in config:
            runcontrol = config[runcontrol_sec]
        else:
            logger.info('No runcontrol for {}'.format(self.run_type))
            return

        self.analysis_classes = self.suite.analysis_classes

        for ordered_analysis, enabled_str in sorted(runcontrol.items()):
            analysis = ordered_analysis[3:]
            enabled = enabled_str == 'True'
            # N.B. even if analyser not enabled in config, want to make sure it
            # can still be run by e.g. run_analysis.
            if config.has_section(analysis):
                analyser_config = config[analysis]
            else:
                raise OmniumError('NO CONFIG FOR ANALYSIS')

            if analysis not in self.analysis_classes:
                raise OmniumError('COULD NOT FIND ANALYZER: {}'.format(analysis))

            logger.debug(analysis)

            filename_glob = analyser_config['filename']
            logger.debug(filename_glob)

            logger.debug('Adding analysis: {}'.format(analysis))

            if analysis in self.analysis_workflow:
                raise OmniumError('{} already in analysis workflow'.format(analysis))

            self.analysis_workflow[analysis] = (analysis, analyser_config['data_type'],
                                                analyser_config, filename_glob, enabled)

        for analyser_name in self.analysis_classes.keys():
            if analyser_name not in self.analysis_workflow:
                logger.warn('Analyser found but has no config: {}'.format(analyser_name))
        logger.debug(self.analysis_workflow.keys())

    def run_analysis(self, analysis, user_filename_glob=None):
        if not self.analysis_workflow:
            self.gen_analysis_workflow()
        (analysis, data_type, analyser_config,
         filename_glob, enabled) = self.analysis_workflow[analysis]
        if user_filename_glob:
            filename_glob = user_filename_glob
            logger.debug('Using user defined glob: {}'.format(filename_glob))
        self._setup_run_analyser(analysis, data_type, analyser_config, filename_glob)

    def run_all(self):
        logger.debug('running all analysis')
        for (analysis, data_type, analyser_config,
             filename_glob, enabled) in self.analysis_workflow.values():
            if enabled:
                logger.debug('analysis {} enabled'.format(analysis))
                self._setup_run_analyser(analysis, data_type, analyser_config, filename_glob)

    def get_filenames(self, analysis, data_type, filename_glob):
        Analyser = self.analysis_classes[analysis]

        multi_file = Analyser.multi_file
        multi_expt = Analyser.multi_expt

        if data_type == 'datam':
            data_dir = self.atmos_datam_dir
        elif data_type == 'dataw':
            data_dir = self.atmos_dataw_dir
        if multi_expt:
            # N.B. multi_file == 'False'
            yield self.expts, [filename_glob]
        else:
            for expt in self.expts:
                filenames = Analyser.get_files(data_dir[expt], filename_glob)
                if multi_file:
                    yield [expt], filenames
                else:
                    for filename in filenames:
                        yield [expt], [filename]

    def _setup_run_analyser(self, analysis, data_type, analyser_config, filename_glob):
        Analyser = self.analysis_classes[analysis]
        logger.info('Running {}: {}, {}'.format(Analyser.analysis_name, self.expts, filename_glob))

        multi_file = Analyser.multi_file
        multi_expt = Analyser.multi_expt

        if multi_file and multi_expt:
            raise OmniumError('Only one of multi_file, multi_expt can be True')

        for expts, filenames in self.get_filenames(analysis, data_type, filename_glob):
            logger.info('  Running {}: {}: {}'.format(Analyser.analysis_name, expts, filenames))
            self._run_analyser(Analyser, data_type, analyser_config,
                               filenames, expts, multi_file, multi_expt)

    def _run_analyser(self, Analyser, data_type, analyser_config,
                      filenames, expts, multi_file, multi_expt):
        if data_type == 'datam':
            data_dir = self.atmos_datam_dir
        elif data_type == 'dataw':
            data_dir = self.atmos_dataw_dir

        if multi_expt:
            results_dir = os.path.join(self.suite.suite_dir, 'share/data/history/suite_results')
        else:
            results_dir = data_dir[expts[0]]

        expt_group = self.settings.get('expt_group', None)
        analyser = Analyser(self.suite, data_type, data_dir, results_dir,
                            filenames, expts, expt_group)
        analyser.set_config(analyser_config)

        if self.display_only:
            logger.info('  Display results only')
            analyser.load_results()
            analyser.display(self.interactive)
        elif not analyser.already_analysed() or analyser.force or self.force:
            analyser.load()
            analyser.run(self.interactive)
            analyser.save(self.state, self.suite)
            analyser.display(self.interactive)
        else:
            logger.info('  Analysis already run')
        return analyser
