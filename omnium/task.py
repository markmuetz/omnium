import fnmatch
import os
import glob
from logging import getLogger

from omnium.omnium_errors import OmniumError
from omnium.version import get_version

logger = getLogger('om.task')


class Task(object):
    def __init__(self, index, expt, runid, run_type, task_type, analysis_name,
                 filenames, output_filenames):
        self.index = index
        if run_type == 'suite':
            self.expts = expt
        self.expt = expt
        self.run_type = run_type
        self.runid = runid
        self.task_type = task_type
        self.analysis_name = analysis_name
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
                                                                 self.analysis_name,
                                                                 self.filenames,
                                                                 self.output_filenames)


class TaskMaster(object):
    def __init__(self, suite, run_type, analysis_workflow, expts, settings_name, force):
        self.all_tasks = []
        """All tasks that have been generated in runable order."""
        self.virtual_dir = []
        """Virtual directory that initially mirrors real input dirs, and is filled up
        with files that will be created by each task."""

        self._suite = suite
        self._run_type = run_type
        self._analysis_workflow = analysis_workflow
        self._expts = expts
        self._settings_name = settings_name
        self._force = force

        self._pending_tasks = []
        self._filename_task_map = {}
        self._working_tasks = []
        self._completed_tasks = []

    def get_next_pending(self):
        if self._pending_tasks:
            task = self._pending_tasks.pop(0)
            assert task.status == 'pending'
            task.status = 'working'
            self._working_tasks.append(task)
            logger.debug('get working task {}', task.index)
            return task
        else:
            # Either there are no currently pending tasks with all deps fulfilled,
            # or I'm finished.
            if len(self._completed_tasks) + len(self._working_tasks) == len(self.all_tasks):
                logger.debug('all tasks completed or being worked on')
                raise StopIteration
            else:
                logger.debug('no tasks available but not finished yet')
                return None

    def update_task(self, task_index, task_status):
        logger.debug('updating task {} to {}', task_index, task_status)
        existing_task = self.all_tasks[task_index]
        existing_task.status = task_status
        if task_status == 'done':
            self._working_tasks.remove(existing_task)
            self._completed_tasks.append(existing_task)
            logger.debug('{} tasks completed', len(self._completed_tasks))

        for next_task in existing_task.next_tasks:
            if all([pt.status == 'done' for pt in next_task.prev_tasks]):
                if next_task not in self._pending_tasks:
                    next_task.status = 'pending'
                    self._pending_tasks.append(next_task)
                    logger.debug('adding pending task {}', next_task.index)

    def get_all_tasks(self):
        while True:
            # Will raise StopIteration when no more left.
            yield self.get_next_pending()

    def print_tasks(self):
        for task in self.all_tasks:
            print(task)

    def gen_tasks_for_analysis(self, analyser_cls):
        if self._run_type == 'cmd':
            for expt in self._expts:
                self.gen_cmd_tasks(analyser_cls)
        elif self._run_type == 'cycle':
            for expt in self._expts:
                self.gen_cycle_tasks(expt, analyser_cls)
        elif self._run_type == 'expt':
            for expt in self._expts:
                self.gen_expt_tasks(expt, analyser_cls)
        elif self._run_type == 'suite':
            self.gen_suite_tasks(analyser_cls)

    def gen_all_tasks(self):
        logger.debug('generating all tasks for {}', self._run_type)
        enabled_analysis = [a for a in self._analysis_workflow.values() if a[2]]
        self._scan_data_dirs(enabled_analysis)

        for analysis_name, analyser_cls, enabled in enabled_analysis:
            self.gen_tasks_for_analysis(analyser_cls)

        self._find_pending()
        logger.info('Generated {} tasks', len(self.all_tasks))

    def gen_single_analysis_tasks(self, analysis_name, filenames):
        logger.debug('generating single analysis tasks for {}', self._run_type)
        all_analysis = self._analysis_workflow.values()
        if filenames:
            self._find_filenames(filenames)
        else:
            self._scan_data_dirs(all_analysis)
        # N.B. ignores analysis enabled status.

        for search_analysis_name, analyser_cls, enabled in all_analysis:
            if analysis_name == search_analysis_name:
                self.gen_tasks_for_analysis(analyser_cls)

        self._find_pending()
        logger.info('Generated {} tasks', len(self.all_tasks))

    def gen_cmd_tasks(self, analyser_cls):
        assert analyser_cls.single_file or analyser_cls.multi_file
        logger.debug('generating cmd tasks for {}', analyser_cls.analysis_name)

        logger.debug('using files: {}', self.virtual_dir)

        if analyser_cls.single_file:
            self._gen_single_file_tasks(None, analyser_cls, self.virtual_dir)
        elif analyser_cls.multi_file:
            self._gen_multi_file_tasks(None, analyser_cls, self.virtual_dir)

    def gen_cycle_tasks(self, expt, analyser_cls):
        assert analyser_cls.single_file
        logger.debug('generating cycle tasks for {}', analyser_cls.analysis_name)

        done_filenames = self._find_done_filenames(expt, analyser_cls)

        self._gen_single_file_tasks(expt, analyser_cls, done_filenames)

    def gen_expt_tasks(self, expt, analyser_cls):
        assert analyser_cls.single_file or analyser_cls.multi_file
        logger.debug('generating expt tasks for {}', analyser_cls.analysis_name)

        done_filenames = self._find_done_filenames(expt, analyser_cls)

        if analyser_cls.single_file:
            self._gen_single_file_tasks(expt, analyser_cls, done_filenames)
        elif analyser_cls.multi_file:
            self._gen_multi_file_tasks(expt, analyser_cls, done_filenames)

    def gen_suite_tasks(self, analyser_cls):
        logger.debug('generating suite tasks for {}', analyser_cls.analysis_name)
        assert analyser_cls.multi_expt
        filenames = []
        for expt in self._expts:
            done_filenames = self._find_done_filenames(expt, analyser_cls)
            assert len(done_filenames) <= 1
            if done_filenames:
                filenames.append(done_filenames[0])

        if not filenames:
            logger.debug('found no files for {}', analyser_cls.analysis_name)
            return

        assert len(filenames) == len(self._expts)

        # N.B. output filename for suite tasks cannot contain {expt} - this will raise an error if
        # it does.
        dir_vars = {'version_dir': self._get_version_dir(analyser_cls),
                    'expts': '_'.join(self._expts)}
        output_filenames = self._gen_output_filenames(analyser_cls, dir_vars)
        runid = None
        task = Task(len(self.all_tasks), self._expts, runid, 'suite', 'analysis',
                    analyser_cls.analysis_name,
                    filenames, output_filenames)

        for filename in filenames:
            if filename in self._filename_task_map:
                prev_task = self._filename_task_map[filename]
                prev_task.add_next(task)

        for output_filename in task.output_filenames:
            self._filename_task_map[output_filename] = task

        self.all_tasks.append(task)
        self.virtual_dir.extend(task.output_filenames)
        self.virtual_dir.extend([fn + '.done' for fn in task.output_filenames])

    def _find_pending(self):
        for task in self.all_tasks:
            if all([pt.status == 'done' for pt in task.prev_tasks]):
                self._pending_tasks.append(task)

        logger.debug('{} pending tasks', len(self._pending_tasks))

    def _scan_data_dirs(self, analysis):
        dirs_to_scan = []
        for expt in self._expts:
            for analysis_name, analyser_cls, enabled in analysis:
                dir_vars = {'expt': expt,
                            'version_dir': self._get_version_dir(analyser_cls)}
                # TODO: this *might* miss some files if it is not def'd using '{input_dir}/...'
                input_dir = os.path.join(self._suite.suite_dir,
                                         analyser_cls.input_dir.format(**dir_vars))
                dirs_to_scan.append(input_dir)

        # Ensure uniqueness.
        dirs_to_scan = set(dirs_to_scan)
        for dir in dirs_to_scan:
            logger.debug('Scanning dir: {}', dir)
            found_filenames = sorted(glob.glob(os.path.join(dir, '*')))
            self.virtual_dir.extend(found_filenames)
        self.virtual_dir = sorted(list(set(self.virtual_dir)))

    def _find_filenames(self, filenames):
        for filename in filenames:
            if not os.path.exists(filename):
                raise OmniumError('{} does not exist'.format(filename))
            self.virtual_dir.append(os.path.abspath(filename))

    def _gen_single_file_tasks(self, expt, analyser_cls, done_filenames):
        dir_vars = {'expt': expt, 'version_dir': self._get_version_dir(analyser_cls)}

        if not done_filenames:
            logger.debug('no files for {}', analyser_cls.analysis_name)
            return

        logger.debug('single file analysis')

        for filtered_filename in done_filenames:
            if analyser_cls.uses_runid:
                runid = analyser_cls.get_runid(filtered_filename)
                if not (analyser_cls.min_runid <= runid <= analyser_cls.max_runid):
                    logger.debug('file {} out of runid range: {} - {}',
                                 filtered_filename, analyser_cls.min_runid, analyser_cls.max_runid)
                    continue
                dir_vars['runid'] = runid
            else:
                runid = None

            output_filenames = self._gen_output_filenames(analyser_cls, dir_vars)
            task = Task(len(self.all_tasks), expt, runid, self._run_type, 'analysis',
                        analyser_cls.analysis_name,
                        [filtered_filename], output_filenames)
            logger.debug(task)
            if filtered_filename in self._filename_task_map:
                prev_task = self._filename_task_map[filtered_filename]
                prev_task.add_next(task)
            for output_filename in task.output_filenames:
                self._filename_task_map[output_filename] = task
            self.all_tasks.append(task)
            # Don't fill up virtual_dir if cmd.
            if self._run_type != 'cmd':
                # Check output filenames don't exist.
                for output_filename in task.output_filenames:
                    if os.path.exists(output_filename):
                        if not self._force:
                            msg = 'output file {} already exists'
                            logger.debug(msg, output_filename)
                        else:
                            msg = 'output file {} will be overwritten'
                            logger.debug(msg, output_filename)
                    else:
                        self.virtual_dir.append(output_filename)
                        self.virtual_dir.append(output_filename + '.done')

            if analyser_cls.delete:
                logger.debug('will delete file: {}', filtered_filename)
                self.virtual_dir.remove(filtered_filename)

    def _gen_output_filenames(self, analyser_cls, dir_vars):
        output_filenames = []
        dir_vars['output_dir'] = analyser_cls.output_dir.format(**dir_vars)
        for output_filename in analyser_cls.output_filenames:
            output_filenames.append(os.path.join(self._suite.suite_dir,
                                                 output_filename.format(**dir_vars)))
        return output_filenames

    def _gen_multi_file_tasks(self, expt, analyser_cls, done_filenames):
        dir_vars = {'expt': expt, 'version_dir': self._get_version_dir(analyser_cls)}
        if not done_filenames:
            logger.debug('no files for {}', analyser_cls.analysis_name)
            return

        logger.debug('multi file analysis')

        runid = 0

        output_filenames = self._gen_output_filenames(analyser_cls, dir_vars)
        task = Task(len(self.all_tasks), expt, runid, self._run_type, 'analysis',
                    analyser_cls.analysis_name,
                    done_filenames, output_filenames)
        for filtered_filename in done_filenames:
            if filtered_filename in self._filename_task_map:
                prev_task = self._filename_task_map[filtered_filename]
                prev_task.add_next(task)

        for output_filename in task.output_filenames:
            self._filename_task_map[output_filename] = task
        self.all_tasks.append(task)
        for output_filename in task.output_filenames:
            # Check output filenames don't exist.
            if os.path.exists(output_filename):
                if not self._force:
                    msg = 'output file {} already exists'
                    logger.debug(msg, output_filename)
                else:
                    msg = 'output file {} will be overwritten'
                    logger.debug(msg, output_filename)
            else:
                self.virtual_dir.append(output_filename)
                self.virtual_dir.append(output_filename + '.done')
        logger.debug(task)

    def _find_done_filenames(self, expt, analyser_cls):
        dir_vars = {'version_dir': self._get_version_dir(analyser_cls)}
        if expt:
            dir_vars['expt'] = expt
        dir_vars['input_dir'] = analyser_cls.input_dir.format(**dir_vars)

        if analyser_cls.input_filename_glob:
            filename_glob = os.path.join(self._suite.suite_dir,
                                         analyser_cls.input_filename_glob.format(**dir_vars))
            filtered_filenames = sorted(fnmatch.filter(self.virtual_dir, filename_glob))
        elif analyser_cls.input_filenames or analyser_cls.input_filename:
            if analyser_cls.input_filename:
                input_filenames = [analyser_cls.input_filename]
            else:
                input_filenames = analyser_cls.input_filenames

            filtered_filenames = []
            for fn in input_filenames:
                filename = os.path.join(self._suite.suite_dir, fn.format(**dir_vars))
                fns = sorted(fnmatch.filter(self.virtual_dir, filename))
                filtered_filenames.extend(fns)
            if len(input_filenames) != len(filtered_filenames):
                raise OmniumError('Could not find all filenames for {}'
                                  .format(analyser_cls.analysis_name))
        else:
            raise OmniumError('{} must have one of these set: '
                              'input_filename_glob, input_filenames, input_filename'
                              .format(analyser_cls))
        done_filenames = [fn for fn in filtered_filenames if fn + '.done' in self.virtual_dir]
        logger.debug('found files: {}', done_filenames)
        return done_filenames

    def _get_version_dir(self, analyser_cls):
        _, settings = self._suite.analysers.get_settings(analyser_cls, self._settings_name)
        package = self._suite.analysers.get_package(analyser_cls)
        omnium_version = 'om_v' + get_version(form='medium')
        package_version = self._get_package_version(package)
        version = omnium_version + '_' + package_version
        version_dir = version + '_' + settings.get_hash()[:10]

        return version_dir

    @staticmethod
    def _get_package_version(package):
        return package.__name__ + '_v' + get_version(package.__version__, form='medium')
