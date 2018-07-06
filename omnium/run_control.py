import os
from collections import OrderedDict
from logging import getLogger

from omnium.omnium_errors import OmniumError
from omnium.state import State
from omnium.task import TaskMaster
from omnium.setup_logging import add_file_logging, remove_file_logging
from omnium.analyser_setting import AnalyserSetting

logger = getLogger('om.run_ctrl')


class RunControl(object):
    def __init__(self, suite, run_type, expts, settings_name,
                 production=False, force=False, no_run_if_started=False):
        self.suite = suite
        self.production = production

        self.run_type = run_type
        if self.run_type in ['cmd', 'suite']:
            self.expts = expts
        else:
            self.expts = expts

        self.settings_name = settings_name
        self.force = force
        self.no_run_if_started = no_run_if_started

        self.analysis_workflow = OrderedDict()
        self.full_analysis_workflow = OrderedDict()
        self.analysis_classes = self.suite.analysis_classes

        logger.warning('Disabling Python warnings')
        import warnings
        warnings.filterwarnings("ignore")
        self.state = State()

        if self.production:
            logger.debug('running in production mode')
            if self.state.git_status != 'clean':
                raise OmniumError('omnium is not clean, not running')
            for status in self.suite.analysis_status:
                if status != 'clean':
                    raise OmniumError('omnium analysis not all clean clean, not running')

    def __repr__(self):
        return 'RunControl({}, "{}", {})'.format(repr(self.suite), self.run_type, self.expts)

    def print_setup(self):
        for attr in ['run_type', 'expts']:
            print('{}: {}'.format(attr, getattr(self, attr)))

    def print_tasks(self):
        self.task_master.print_tasks()

    def gen_analysis_workflow(self):
        config = self.suite.app_config
        for run_type in ['cmd', 'cycle', 'expt', 'suite']:
            analysis_workflow = OrderedDict()
            runcontrol_sec = 'runcontrol_{}'.format(run_type)
            if runcontrol_sec in config:
                runcontrol = config[runcontrol_sec]
            else:
                logger.info('No runcontrol for {}', run_type)
                continue

            for ordered_analysis, enabled_str in sorted(runcontrol.items()):
                analysis_name = ordered_analysis[3:]
                logger.debug('analysis: {}', analysis_name)
                enabled = enabled_str == 'True'

                if analysis_name not in self.analysis_classes:
                    raise OmniumError('COULD NOT FIND ANALYSER: {}'.format(analysis_name))

                if analysis_name in analysis_workflow:
                    raise OmniumError('{} already in analysis workflow'.format(analysis_name))

                analyser_cls = self.analysis_classes[analysis_name]
                self.full_analysis_workflow[analysis_name] = (analysis_name, analyser_cls, enabled)
                analysis_workflow[analysis_name] = (analysis_name, analyser_cls, enabled)

            logger.debug('{}: {}', run_type, analysis_workflow.keys())
            if run_type == self.run_type:
                if run_type != 'cmd':
                    self.analysis_workflow = analysis_workflow

        if self.run_type == 'cmd':
            # When running as cmd want all the analysis available.
            self.analysis_workflow = self.full_analysis_workflow

        for analyser_name in self.analysis_classes.keys():
            if analyser_name not in self.full_analysis_workflow:
                logger.debug('analyser_cls found but has no config: {}', analyser_name)

    def gen_tasks(self):
        self.task_master = TaskMaster(self.suite, self.run_type, self.analysis_workflow, self.expts,
                                      self.settings_name, self.force)
        self.task_master.gen_all_tasks()

    def gen_tasks_for_analysis(self, analysis_name, filenames):
        self.task_master = TaskMaster(self.suite, self.run_type, self.analysis_workflow, self.expts,
                                      self.settings_name, self.force)
        self.task_master.gen_single_analysis_tasks(analysis_name, filenames)

    def run_all(self):
        logger.debug('running all analysis')

        run_count = 0
        for task in self.task_master.get_all_tasks():
            if not task:
                # Should not be reached, when called like this should sequentially hand out tasks
                # until there are no more left.
                raise Exception('Task not issued by TaskMaster')
            run_count += 1
            self.run_task(task)
            task.status = 'done'
            self.task_master.update_task(task.index, task.status)
        if not run_count:
            logger.warning('No tasks were run')

    def run_single_analysis(self, analysis_name):
        all_tasks = self.task_master.all_tasks
        tasks_to_run = [t for t in all_tasks if t.analysis_name == analysis_name]
        if not tasks_to_run:
            raise OmniumError('No tasks matching {} found'.format(analysis_name))

        for task in tasks_to_run:
            self.run_task(task)

    def run_task(self, task):
        print_filenames = os.path.basename(task.filenames[0])
        if len(task.filenames) > 1:
            print_filenames += '...' + os.path.basename(task.filenames[-1])
        logger.info('Running task {}: {} - {}:{}',
                    task.index, task.analysis_name, task.expt, print_filenames)
        logger.debug('running: {}', task)
        analyser_cls = self.analysis_classes[task.analysis_name]

        settings_filename_fmt, settings = self.suite.analysers.get_settings(analyser_cls,
                                                                            self.settings_name)
        analyser = analyser_cls(self.suite, task, settings)
        dir_vars = {'version_dir': self.task_master._get_version_dir(analyser_cls)}
        settings_filename = settings_filename_fmt.format(**dir_vars)
        if not os.path.exists(settings_filename):
            if not os.path.exists(os.path.dirname(settings_filename)):
                os.makedirs(os.path.dirname(settings_filename))
            settings.save(settings_filename)
        else:
            loaded_settings = AnalyserSetting()
            loaded_settings.load(settings_filename)
            assert loaded_settings == settings, 'settings not equal to loaded settings.'

        run_analysis = not analyser.already_analysed()
        if self.no_run_if_started and analyser.already_started_analysing():
            run_analysis = False
        if analyser.force or self.force:
            run_analysis = True
            analyser.force = True

        if run_analysis:
            add_file_logging(analyser.logname, root=False)

            analyser.analysis_load()
            analyser.analysis_run()
            analyser.analysis_save(self.state, self.suite)
            analyser.analysis_display()
            analyser.analysis_done()
            logger.info('Task run: {}', analyser.analysis_name)

            remove_file_logging(analyser.logname)
        else:
            logger.info('Task already run: {}', analyser.analysis_name)

        return analyser
