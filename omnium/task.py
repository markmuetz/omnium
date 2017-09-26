import os
from glob import glob
import fnmatch
from copy import copy
from omnium.converters import CONVERTERS


class Task(object):
    def __init__(self, expt, cycle, task_type, name, filenames, output_filenames):
        self.expt = expt
        self.cycle = cycle
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
        return 'Task("{}", "{}", "{}", "{}", {}, {})'.format(self.expt,
                                                             self.cycle,
                                                             self.task_type,
                                                             self.name,
                                                             self.filenames,
                                                             self.output_filenames)


class TaskMaster(object):
    def __init__(self, suite, settings, analysis_workflow, expts, atmos_datam_dir, atmos_dataw_dir, converter=None):
        self.suite = suite
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
                output_filename = self.converter._converted_filename(filename)
                task = Task(expt, 'cycle', 'conversion', self.converter.name, [filename], [output_filename])
                self.all_tasks.append(task)
                for output_filename in task.output_filenames:
                    self.filename_task_map[output_filename] = task
                self.pending_tasks.append(task)
                self.output_filenames.extend(task.output_filenames)

    def gen_initial_tasks(self, expt, analysis_name, Analyser, enabled):
        if enabled:
            analysis_config = self.config[analysis_name]
            data_type = analysis_config['data_type']
            if data_type == 'datam':
                data_dir = self.atmos_datam_dir[expt]
            elif data_type == 'dataw':
                data_dir = self.atmos_dataw_dir[expt]
            filename_glob = analysis_config['filename']
            input_filenames = sorted(glob(os.path.join(data_dir, filename_glob)))
            self.output_filenames.extend(copy(input_filenames))

            for input_filename in input_filenames:
                if os.path.exists(input_filename + '.done'):
                    # assert(input_filename not in self.filename_task_map)
                    split_filename = input_filename.split('.')
                    output_filename = Analyser.gen_output_filename(False,
                                                                   analysis_name,
                                                                   'atmos',
                                                                   data_type,
                                                                   split_filename)
                    task = Task(expt, 'cycle', 'analysis', analysis_name, [input_filename], [os.path.join(data_dir, output_filename)])
                    self.all_tasks.append(task)
                    for output_filename in task.output_filenames:
                        self.filename_task_map[output_filename] = task
                    self.pending_tasks.append(task)
                    self.output_filenames.extend(task.output_filenames)

    def gen_subsequent_tasks(self, expt, analysis_name, Analyser, enabled):
        if enabled:
            # TODO: DRY:.
            analysis_config = self.config[analysis_name]
            data_type = analysis_config['data_type']
            if data_type == 'datam':
                data_dir = self.atmos_datam_dir[expt]
            elif data_type == 'dataw':
                data_dir = self.atmos_dataw_dir[expt]
            analysis_config = self.config[analysis_name]
            filename_glob = analysis_config['filename']
            filtered_filenames = sorted(fnmatch.filter(self.output_filenames, os.path.join(data_dir, filename_glob)))
            for filtered_filename in filtered_filenames:
                # assert(filtered_filename not in self.filename_task_map)
                split_filename = os.path.basename(filtered_filename).split('.')
                output_filename = Analyser.gen_output_filename(False,
                                                               analysis_name,
                                                               'atmos',
                                                               data_type,
                                                               split_filename)
                prev_task = self.filename_task_map[filtered_filename]
                task = Task(expt, 'cycle', 'analysis', analysis_name, [filtered_filename], [os.path.join(data_dir, output_filename)])
                for output_filename in task.output_filenames:
                    self.filename_task_map[output_filename] = task
                self.all_tasks.append(task)
                prev_task.add_next(task)
                self.output_filenames.extend(task.output_filenames)

    def gen_tasks(self):
        for expt in self.expts:
            if self.converter:
                self.gen_converter_tasks(expt)
                subsequent_analysis = self.analysis_workflow.values()
            else:
                analysis_name, Analyser, enabled = self.analysis_workflow.values()[0]
                self.gen_initial_tasks(expt, analysis_name, Analyser, enabled)
                subsequent_analysis = self.analysis_workflow.values()[1:]

            for analysis_name, Analyser, enabled in subsequent_analysis:
                self.gen_subsequent_tasks(expt, analysis_name, Analyser, enabled)
