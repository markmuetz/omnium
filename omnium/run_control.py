import os
from glob import glob
from collections import OrderedDict
from logging import getLogger

from omnium.converters import CONVERTERS
from omnium.omnium_errors import OmniumError
from omnium.state import State
from omnium.task import TaskMaster

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

        self.config = self.suite.app_config
        run_type = self.run_type

        settings_sec = 'settings_{}'.format(run_type)

        self.settings = self.config[settings_sec]

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

    def print_tasks(self):
        self.task_master.print_tasks()

    def gen_analysis_workflow(self):
        self.analysis_workflow = OrderedDict()
        config = self.config

        runcontrol_sec = 'runcontrol_{}'.format(self.run_type)
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

            Analyser = self.analysis_classes[analysis]
            self.analysis_workflow[analysis] = (analysis, Analyser, enabled)

        for analyser_name in self.analysis_classes.keys():
            if analyser_name not in self.analysis_workflow:
                logger.warn('Analyser found but has no config: {}'.format(analyser_name))
        logger.debug(self.analysis_workflow.keys())

    def gen_tasks(self):
        convert = self.settings.getboolean('convert', False)
        if convert:
            converter_name = self.settings.get('converter', 'ff2nc')
        else:
            converter_name = None
        self.task_master = TaskMaster(self.suite, self.run_type, self.settings, self.analysis_workflow,
                                      self.expts, self.atmos_datam_dir, self.atmos_dataw_dir,
                                      converter_name)
        self.task_master.gen_all_tasks()

    def run_all(self):
        logger.debug('running all analysis')

        for task in self.task_master.get_all_tasks():
            self.run_task(task)

    def run_task(self, task):
        logger.debug(task)
        if task.task_type == 'conversion':
            self.run_conversion(task)
        elif task.task_type == 'analysis':
            self.run_analysis(task)

    def run_conversion(self, task):
        overwrite = self.settings.getboolean('overwrite', False)
        delete = self.settings.getboolean('delete', False)
        converter = CONVERTERS[task.name](overwrite, delete)
        filenames_for_conversion = []
        for filename in task.filenames:
            # Check that file is not being converted by another process.
            if os.path.exists(filename + '.converting'):
                logger.warn('  Already being converted: {}'.format(filename))
            else:
                with open(filename + '.converting', 'w') as f:
                    f.write('Converting with {}\n'.format(task.name))
                filenames_for_conversion.append(filename)

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

    def run_analysis(self, task):
        Analyser = self.analysis_classes[task.name]

        multi_file = Analyser.multi_file
        multi_expt = Analyser.multi_expt

        results_dir = os.path.dirname(task.output_filenames[0])
        expt_group = self.settings.get('expt_group', None)

        analyser = Analyser(self.suite, task, results_dir, expt_group)
        analyser.set_config(self.config[task.name])

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
