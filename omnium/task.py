import os
from glob import glob
import fnmatch
from logging import getLogger

from copy import copy
from omnium.converters import CONVERTERS

logger = getLogger('om.task')


class Task(object):
    def __init__(self, index, expt, run_type, task_type, name, filenames, output_filenames):
        self.index = index
        if run_type == 'suite':
            self.expts = expt
        self.expt = expt
        self.run_type = run_type
        self.task_type = task_type
        self.name = name
        self.filenames = filenames
        self.output_filenames = output_filenames
        self.status = 'pending'
        self.prev_tasks = []
        self.next_tasks = []

    def add_next(self, task):
        self.next_tasks.append(task)
        task.prev_tasks.append(self)

    def __repr__(self):
        return 'Task({}, "{}", "{}", "{}", "{}", {}, {})'.format(self.index, self.expt,
                                                                 self.run_type,
                                                                 self.task_type,
                                                                 self.name,
                                                                 self.filenames,
                                                                 self.output_filenames)


class TaskMaster(object):
    def __init__(self, suite, run_type, settings, analysis_workflow, expts,
                 atmos_datam_dir, atmos_dataw_dir, converter=None):
        self.suite = suite
        self.run_type = run_type
        self.settings = settings
        self.config = suite.app_config
        self.analysis_workflow = analysis_workflow
        self.expts = expts
        self.atmos_datam_dir = atmos_datam_dir
        self.atmos_dataw_dir = atmos_dataw_dir
        self.converter = CONVERTERS[converter] if converter else None

        self.all_tasks = []
        self.pending_tasks = []
        self.output_filenames = []
        self.filename_task_map = {}
        self.working_tasks = []
        self.completed_tasks = []

    def get_next_pending(self):
        if self.pending_tasks:
            task = self.pending_tasks.pop(0)
            task.status = 'working'
            self.working_tasks.append(task)
            logger.debug('get working task {}'.format(task.index))
            return task
        else:
            # Either there are no currently pending tasks with all deps fulfilled,
            # or I'm finished.
            if len(self.completed_tasks) + len(self.working_tasks) == len(self.all_tasks):
                logger.debug('all tasks completed or being worked on')
                raise StopIteration
            else:
                logger.debug('no tasks available but not finished yet')
                return None

    def update_task(self, task_index, task_status):
        logger.debug('updating task {} to {}'.format(task_index, task_status))
        existing_task = self.all_tasks[task_index]
        existing_task.status = task_status
        if task_status == 'done':
            self.working_tasks.remove(existing_task)
            self.completed_tasks.append(existing_task)
            logger.debug('{} tasks completed'.format(len(self.completed_tasks)))

        for next_task in existing_task.next_tasks:
            if all([pt.status == 'done' for pt in next_task.prev_tasks]):
                self.pending_tasks.append(next_task)
                logger.debug('adding pending task {}'.format(next_task.index))

    def get_all_tasks(self):
        for task in self.all_tasks:
            yield task

    def print_tasks(self):
        for task in self.all_tasks:
            print(task)

    def gen_converter_tasks(self, expt):
        data_dir = self.atmos_datam_dir[expt]
        print(self.settings)
        filename_globs = self.settings['filenames'].split(',')
        for filename_glob in filename_globs:
            filenames = sorted(glob(os.path.join(data_dir, filename_glob)))
            for filename in filenames:
                # assert(filename not in self.filename_task_map)
                if os.path.exists(os.path.join(data_dir, filename + '.done')):
                    output_filename = self.converter._converted_filename(filename)
                    task = Task(len(self.all_tasks), expt, self.run_type, 'conversion', self.converter.name,
                                [filename], [output_filename])
                    self.all_tasks.append(task)
                    for output_filename in task.output_filenames:
                        self.filename_task_map[output_filename] = task
                    self.output_filenames.extend(task.output_filenames)

    def gen_tasks(self, initial, expt, analysis_name, Analyser):
        logger.debug('generating tasks for {}'.format(analysis_name))
        analysis_config = self.config[analysis_name]
        data_type = analysis_config['data_type']
        if data_type == 'datam':
            data_dir = self.atmos_datam_dir[expt]
        elif data_type == 'dataw':
            data_dir = self.atmos_dataw_dir[expt]
        analysis_config = self.config[analysis_name]
        filename_glob = analysis_config['filename']
        logger.debug('using data_dir: {}'.format(data_dir))
        logger.debug('using filename_glob: {}'.format(filename_glob))
        if initial:
            filtered_filenames = sorted(glob(os.path.join(data_dir, filename_glob)))
            self.output_filenames.extend(copy(filtered_filenames))
            logger.debug('found initial files: {}'.format(filtered_filenames))
        else:
            filtered_filenames = sorted(fnmatch.filter(self.output_filenames,
                                                       os.path.join(data_dir, filename_glob)))
            logger.debug('found files: {}'.format(filtered_filenames))

        if Analyser.multi_file:
            logger.debug('multi file analysis')

            split_filename = os.path.basename(filtered_filenames[0]).split('.')
            output_filename = Analyser.gen_output_filename(True,
                                                           analysis_name,
                                                           'atmos',
                                                           data_type,
                                                           split_filename)
            task = Task(len(self.all_tasks), expt, self.run_type, 'analysis', analysis_name,
                        filtered_filenames, [os.path.join(data_dir, output_filename)])
            if not initial:
                for filtered_filename in filtered_filenames:
                    prev_task = self.filename_task_map[filtered_filename]
                    prev_task.add_next(task)

            for output_filename in task.output_filenames:
                self.filename_task_map[output_filename] = task
            self.all_tasks.append(task)
            self.output_filenames.extend(task.output_filenames)
            logger.debug(task)
        else:
            logger.debug('single file analysis')
            for filtered_filename in filtered_filenames:
                if initial and not os.path.exists(os.path.join(data_dir, filtered_filename + '.done')):
                    # Skip files that don't have a .done file if it's an initial task.
                    continue
                # assert(filtered_filename not in self.filename_task_map)
                split_filename = os.path.basename(filtered_filename).split('.')
                output_filename = Analyser.gen_output_filename(False,
                                                               analysis_name,
                                                               'atmos',
                                                               data_type,
                                                               split_filename)
                task = Task(len(self.all_tasks), expt, self.run_type, 'analysis', analysis_name,
                            [filtered_filename], [os.path.join(data_dir, output_filename)])
                if not initial:
                    prev_task = self.filename_task_map[filtered_filename]
                    prev_task.add_next(task)
                for output_filename in task.output_filenames:
                    self.filename_task_map[output_filename] = task
                self.all_tasks.append(task)
                self.output_filenames.extend(task.output_filenames)
                logger.debug(task)

    def gen_suite_tasks(self, initial, expts, analysis_name, Analyser):
        filenames = []
        analysis_config = self.config[analysis_name]
        data_type = analysis_config['data_type']
        analysis_config = self.config[analysis_name]
        filename_glob = analysis_config['filename']

        for expt in expts:
            if data_type == 'datam':
                data_dir = self.atmos_datam_dir[expt]
            elif data_type == 'dataw':
                data_dir = self.atmos_dataw_dir[expt]
            if initial:
                filtered_filenames = sorted(glob(os.path.join(data_dir, filename_glob)))
                self.output_filenames.extend(copy(filtered_filenames))
            else:
                filtered_filenames = sorted(fnmatch.filter(self.output_filenames,
                                                           os.path.join(data_dir, filename_glob)))
                filtered_filenames.extend(sorted(glob(os.path.join(data_dir, filename_glob))))
            assert len(filtered_filenames) == 1
            filenames.append(filtered_filenames[0])

        res_dir = os.path.join(self.suite.suite_dir, 'share/data/history/suite_output')
        split_filename = os.path.basename(filenames[0]).split('.')
        output_filename = Analyser.gen_output_filename(True,
                                                       analysis_name,
                                                       'atmos',
                                                       data_type,
                                                       split_filename)
        task = Task(len(self.all_tasks), expts, 'suite', 'analysis', analysis_name,
                    filenames, [os.path.join(res_dir, output_filename)])

        if not initial:
            # TODO: how to handle deps for suite tasks?
            for filtered_filename in filtered_filenames:
                prev_task = self.filename_task_map[filtered_filename]
                prev_task.add_next(task)

        for output_filename in task.output_filenames:
            self.filename_task_map[output_filename] = task
        self.all_tasks.append(task)
        self.output_filenames.extend(task.output_filenames)

    def find_pending(self):
        for task in self.all_tasks:
            if all([pt.status == 'done' for pt in task.prev_tasks]):
                self.pending_tasks.append(task)

        logger.debug('{} pending tasks'.format(len(self.pending_tasks)))

    def gen_all_tasks(self):
        logger.debug('generating all tasks for {}'.format(self.run_type))
        enabled_analysis = [a for a in self.analysis_workflow.values() if a[2]]
        if self.run_type in ['cycle', 'expt']:
            for expt in self.expts:
                logger.debug('generating tasks for {}'.format(expt))
                if self.converter:
                    logger.debug('convert: {}'.format(self.converter))
                    self.gen_converter_tasks(expt)
                    subsequent_analysis = enabled_analysis
                else:
                    # TODO: Need to be smarter about which tasks are initial and which are subsequent.
                    analysis_name, Analyser, enabled = enabled_analysis[0]
                    logger.debug('initial analysis: {}'.format(analysis_name))
                    self.gen_tasks(True, expt, analysis_name, Analyser)
                    subsequent_analysis = enabled_analysis[1:]

                for analysis_name, Analyser, enabled in subsequent_analysis:
                    logger.debug('subsequent analysis: {}'.format(analysis_name))
                    self.gen_tasks(False, expt, analysis_name, Analyser)
        elif self.run_type == 'suite':
            analysis_name, Analyser, enabled = enabled_analysis[0]
            logger.debug('initial analysis: {}'.format(analysis_name))
            self.gen_suite_tasks(True, self.expts, analysis_name, Analyser)
            subsequent_analysis = enabled_analysis[1:]
            for analysis_name, Analyser, enabled in subsequent_analysis:
                logger.debug('subsequent analysis: {}'.format(analysis_name))
                self.gen_suite_tasks(False, self.expts, analysis_name, Analyser)

        self.find_pending()
        logger.info('Generated {} tasks'.format(len(self.all_tasks)))
