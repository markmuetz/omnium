import glob
import os
from collections import OrderedDict
from logging import getLogger

import omnium
from omnium.analysis import AnalysisSettings
from omnium.omnium_errors import OmniumError
from omnium.pkg_state import PkgState
from omnium.setup_logging import add_file_logging, remove_file_logging
from .task import TaskMaster

logger = getLogger('om.run_ctrl')


def _scan_data_dirs(expts, suite, task_master, analysis):
    virtual_drive = []
    dirs_to_scan = []
    for expt in expts:
        for analysis_name, analyser_cls, enabled in analysis:
            dir_vars = {'expt': expt,
                        'version_dir': task_master.get_version_dir(analyser_cls)}
            # TODO: this *might* miss some files if it is not def'd using '{input_dir}/...'
            input_dir = os.path.join(suite.suite_dir,
                                     analyser_cls.input_dir.format(**dir_vars))
            dirs_to_scan.append(input_dir)

    # Ensure uniqueness.
    dirs_to_scan = set(dirs_to_scan)
    for dir in dirs_to_scan:
        logger.debug('Scanning dir: {}', dir)
        found_filenames = sorted(glob.glob(os.path.join(dir, '*')))
        virtual_drive.extend(found_filenames)
    virtual_drive = sorted(list(set(virtual_drive)))
    return virtual_drive


def _find_filenames(filenames):
    virtual_drive = []
    for filename in filenames:
        if not os.path.exists(filename):
            raise OmniumError('{} does not exist'.format(filename))
        virtual_drive.append(os.path.abspath(filename))
    return virtual_drive


class RunControl(object):
    def __init__(self, suite, run_type, expts, settings_name,
                 production=False, force=False, no_run_if_started=False):
        self._suite = suite
        self._production = production

        self._run_type = run_type
        if self._run_type in ['cmd', 'suite']:
            self._expts = expts
        else:
            self._expts = expts

        self._settings_name = settings_name
        self._force = force
        self._no_run_if_started = no_run_if_started

        self._analysis_workflow = OrderedDict()
        self._full_analysis_workflow = OrderedDict()

        self._state = PkgState(omnium)
        self._task_master = TaskMaster(self._suite, self._run_type, self._settings_name,
                                       self._force)
        self._analysis_pkgs = self._suite.analysis_pkgs

        if self._production:
            logger.info('Running in production mode')
            if self._state.git_status != 'clean':
                raise OmniumError('omnium is not clean, not running')
            for status in self._suite.analysis_status:
                if status != 'clean':
                    raise OmniumError('omnium analysis not all clean clean, not running')
        else:
            logger.warning('Disabling Python warnings')  # oh the irony.
            import warnings
            warnings.filterwarnings("ignore")

    def __repr__(self):
        return 'RunControl({}, "{}", {})'.format(repr(self._suite), self._run_type, self._expts)

    def print_setup(self):
        for attr in ['run_type', 'expts']:
            print('{}: {}'.format(attr, getattr(self, attr)))

    def print_tasks(self):
        self._task_master.print_tasks()

    def gen_analysis_workflow(self):
        config = self._suite.app_config
        for run_type in ['cmd', 'cycle', 'expt', 'suite']:
            analysis_workflow = OrderedDict()
            runcontrol_sec = 'runcontrol_{}'.format(run_type)
            if runcontrol_sec in config:
                runcontrol = config[runcontrol_sec]
            else:
                logger.debug('No runcontrol for {}', run_type)
                continue

            for ordered_analysis, enabled_str in sorted(runcontrol.items()):
                analysis_name = ordered_analysis[3:]
                logger.debug('analysis: {}', analysis_name)
                enabled = enabled_str == 'True'

                if analysis_name not in self._analysis_pkgs.analyser_classes:
                    raise OmniumError('COULD NOT FIND ANALYSER: {}'.format(analysis_name))

                if analysis_name in analysis_workflow:
                    raise OmniumError('{} already in analysis workflow'.format(analysis_name))

                analyser_cls = self._analysis_pkgs.analyser_classes[analysis_name]
                self._full_analysis_workflow[analysis_name] = (analysis_name, analyser_cls, enabled)
                analysis_workflow[analysis_name] = (analysis_name, analyser_cls, enabled)

            logger.debug('{}: {}', run_type, analysis_workflow.keys())
            if run_type == self._run_type:
                if run_type != 'cmd':
                    self._analysis_workflow = analysis_workflow

        if self._run_type == 'cmd':
            # When running as cmd want all the analysis available.
            self._analysis_workflow = self._full_analysis_workflow

    def gen_tasks(self):
        if self._run_type == 'cmd':
            raise OmniumError('Should not call gen_tasks for "cmd": use gen_tasks_for_analysis')
        enabled_analysis = [a for a in self._analysis_workflow.values() if a[2]]
        virtual_drive = _scan_data_dirs(self._expts, self._suite, self._task_master,
                                        enabled_analysis)
        self._task_master.gen_all_tasks(self._expts, virtual_drive, enabled_analysis)

    def gen_tasks_for_analysis(self, analysis_name, filenames=[]):
        if self._run_type == 'cmd' and not filenames:
            raise OmniumError('Must provide filenames for "cmd"')

        if self._run_type == 'cmd':
            virtual_drive = _find_filenames(filenames)
        else:
            virtual_drive = _scan_data_dirs(self._expts, self._suite, self._task_master,
                                            self._analysis_workflow.values())
        self._task_master.gen_single_analysis_tasks(self._expts, virtual_drive,
                                                    self._analysis_workflow, analysis_name)

    def run_all(self):
        logger.debug('running all analysis')

        run_count = 0
        for task in self._task_master.get_all_tasks():
            if not task:
                # Should not be reached, when called like this should sequentially hand out tasks
                # until there are no more left.
                raise Exception('Task not issued by TaskMaster')
            run_count += 1
            self.run_task(task)
            task.status = 'done'
            self._task_master.update_task(task.index, task.status)
        if not run_count:
            logger.warning('No tasks were run')

    def run_single_analysis(self, analysis_name):
        all_tasks = self._task_master.all_tasks
        tasks_to_run = [t for t in all_tasks if t.analysis_name == analysis_name]
        if not tasks_to_run:
            raise OmniumError('No tasks matching {} found'.format(analysis_name))

        for task in tasks_to_run:
            self.run_task(task)

    def _make_analyser(self, task):
        analyser_cls = self._analysis_pkgs.analyser_classes[task.analysis_name]
        settings_filename_fmt, settings = self._analysis_pkgs.get_settings(analyser_cls,
                                                                           self._settings_name)
        analyser = analyser_cls(self._suite, task, settings)
        dir_vars = {'version_dir': self._task_master.get_version_dir(analyser_cls)}
        settings_filename = settings_filename_fmt.format(**dir_vars)
        if not os.path.exists(settings_filename):
            if not os.path.exists(os.path.dirname(settings_filename)):
                os.makedirs(os.path.dirname(settings_filename), exist_ok=True)
            settings.save(settings_filename)
        else:
            loaded_settings = AnalysisSettings()
            loaded_settings.load(settings_filename)
            assert loaded_settings == settings, 'settings not equal to loaded settings.'

        return analyser

    def run_task(self, task):
        print_filenames = os.path.basename(task.filenames[0])
        if len(task.filenames) > 1:
            print_filenames += '...' + os.path.basename(task.filenames[-1])
        logger.info('Running task {}: {} - {}:{}',
                    task.index, task.analysis_name, task.expt, print_filenames)
        logger.debug('running: {}', task)
        analyser = self._make_analyser(task)

        run_analysis = not analyser.already_analysed()
        already_started = False
        if self._no_run_if_started and analyser.already_started_analysing():
            already_started = True
            run_analysis = False
        if analyser.force or self._force:
            run_analysis = True
            analyser.force = True

        if run_analysis:
            add_file_logging(analyser.logname, root=False)

            analyser.analysis_load()
            analyser.analysis_run()
            analyser.analysis_display()
            analyser.analysis_save(self._state, self._suite)
            analyser.analysis_done()
            logger.info('Task run: {}', analyser.analysis_name)

            remove_file_logging(analyser.logname)
        else:
            if already_started:
                logger.info('Task already started: {}', analyser.analysis_name)
            else:
                logger.info('Task already run: {}', analyser.analysis_name)

        return analyser
