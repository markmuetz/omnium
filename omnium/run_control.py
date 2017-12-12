import os
from collections import OrderedDict
from glob import glob
from logging import getLogger

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

        logger.warning('Disabling Python warnings')
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

    def check_setup(self):
        for expt in self.expts:
            data_dir = self.atmos_datam_dir[expt]
            if not os.path.exists(data_dir):
                logger.warning('Dir does not exist: {}'.format(data_dir))
            data_dir = self.atmos_dataw_dir[expt]
            if not os.path.exists(data_dir):
                logger.warning('Dir does not exist: {}'.format(data_dir))

    def print_setup(self):
        for attr in ['run_type', 'expts', 'atmos_datam_dir', 'atmos_dataw_dir']:
            print('{}: {}'.format(attr, getattr(self, attr)))

    def print_tasks(self):
        self.task_master.print_tasks()

    def gen_analysis_workflow(self):
        config = self.config
        self.full_analysis_workflow = OrderedDict()
        self.analysis_classes = self.suite.analysis_classes

        for run_type in ['cycle', 'expt', 'suite']:
            analysis_workflow = OrderedDict()

            runcontrol_sec = 'runcontrol_{}'.format(run_type)
            if runcontrol_sec in config:
                runcontrol = config[runcontrol_sec]
            else:
                logger.info('No runcontrol for {}'.format(run_type))
                continue

            for ordered_analysis, enabled_str in sorted(runcontrol.items()):
                analysis = ordered_analysis[3:]
                logger.debug('analysis: {}'.format(analysis))
                enabled = enabled_str == 'True'
                # N.B. even if analyser not enabled in config, want to make sure it
                # can still be run by e.g. run_analysis.
                if config.has_section(analysis):
                    analyser_config = config[analysis]
                    if 'analysis' in analyser_config:
                        analysis_name = analyser_config['analysis']
                        logger.debug('renamed analysis: {}'.format(analysis_name))
                    else:
                        analysis_name = analysis
                else:
                    raise OmniumError('NO CONFIG FOR ANALYSIS')

                if analysis_name not in self.analysis_classes:
                    raise OmniumError('COULD NOT FIND ANALYZER: {}'.format(analysis_name))

                if analysis_name in analysis_workflow:
                    raise OmniumError('{} already in analysis workflow'.format(analysis_name))

                analyser_cls = self.analysis_classes[analysis_name]
                self.full_analysis_workflow[analysis_name] = (analysis, analyser_cls, enabled)
                analysis_workflow[analysis_name] = (analysis, analyser_cls, enabled)

            logger.debug('{}: {}'.format(run_type, analysis_workflow.keys()))
            if run_type == self.run_type:
                self.analysis_workflow = analysis_workflow

        for analyser_name in self.analysis_classes.keys():
            if analyser_name not in self.full_analysis_workflow:
                logger.debug('analyser_cls found but has no config: {}'.format(analyser_name))

    def gen_tasks(self):
        self.task_master = TaskMaster(self.suite, self.run_type, self.analysis_workflow, self.expts,
                                      self.atmos_datam_dir, self.atmos_dataw_dir)
        self.task_master.gen_all_tasks()

    def run_all(self):
        logger.debug('running all analysis')

        for task in self.task_master.get_all_tasks():
            if not task:
                # Should not be reached, when called like this should sequentially hand out tasks
                # until there are no more left.
                raise Exception('Task not issued by TaskMaster')
            self.run_task(task)
            task.status = 'done'
            self.task_master.update_task(task.index, task.status)

    def run_single_analysis(self, analysis_name, filenames):
        all_tasks = self.task_master.all_tasks
        tasks_to_run = [t for t in all_tasks if t.name == analysis_name]
        if not tasks_to_run:
            raise OmniumError('No tasks matching {} found'.format(analysis_name))

        for task in tasks_to_run:
            if filenames:
                task.filenames = filenames
            self.run_task(task)

    def run_task(self, task):
        logger.debug('running: {}'.format(task))
        analyser_cls = self.analysis_classes[task.name]

        results_dir = os.path.dirname(task.output_filenames[0])
        expt_group = None

        analyser = analyser_cls(self.suite, task, results_dir, expt_group)
        analyser.set_config(self.config[task.config_name])

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
