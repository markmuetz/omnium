import os
from glob import glob
import fnmatch
from copy import copy

class Task(object):
    def __init__(self, expt, cycle, analysis_name, filenames):
        self.status = 'pending'
        self.prev_tasks = []
        self.next_tasks = []

    def add_next(self, task):
        self.next_tasks.append(task)
        task.prev_tasks.append(self)

class TaskMaster(object):
    def __init__(self, suite, analysis_workflow, converter=None):
        self.suite = suite
        self.config = suite.app_config
        self.analysis_workflow = analysis_workflow
        self.converter = converter
        self.all_tasks = []
        self.pending_tasks = []

    def print_tasks(self):
        for task in self.all_tasks:
            print(task)

    def gen_tasks(self):
        analysis_name, Analyser, enabled = self.analysis_workflow.items()[0]
        analysis_config = self.config[analysis_name]
        data_dir = analysis_config['data_dir']
        filename_glob = analysis_config['filename']
        input_filenames = sorted(glob(os.path.join(data_dir, filename_glob)))
        output_filenames = copy(input_filenames)

        filename_task_map = {}
        for input_filename in input_filenames:
            if os.path.extis(input_filename + '.done'):
                task = Task('expt', 'cycle', analysis_name, [input_filename])
                assert(input_filename not in filename_task_map)
                filename_task_map[input_filename] = task
                self.pending_tasks.append(task)

        for analysis_name, Analyser, enabled in self.analysis_workflow.items()[1:]:
            analysis_config = self.config[analysis_name]
            data_dir = analysis_config['data_dir']
            filename_glob = analysis_config['filename']
            filtered_filenames = sorted(fnmatch.filter(output_filenames, filename_glob))
            for filtered_filename in filtered_filenames:
                prev_task = filename_task_map[filtered_filename]
                task = Task('expt', 'cycle', analysis_name, [filtered_filename])
                prev_task.add_next(task)
                output_filenames.extend(task.output_filenames)
