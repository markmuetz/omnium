import fnmatch
import os
import glob
from logging import getLogger

from omnium.omnium_errors import OmniumError

logger = getLogger('om.task')

# TODO: Take into account config for analysis no longer exists!


class Task(object):
    def __init__(self, index, expt, runid, run_type, task_type, name, config_name,
                 filenames, output_filenames):
        self.index = index
        if run_type == 'suite':
            self.expts = expt
        self.expt = expt
        self.run_type = run_type
        self.runid = runid
        self.task_type = task_type
        self.name = name
        self.config_name = config_name
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
    def __init__(self, suite, run_type, analysis_workflow, expts, atmos_datam_dir, atmos_dataw_dir,
                 force):
        self.suite = suite
        self.run_type = run_type
        self.config = suite.app_config
        self.analysis_workflow = analysis_workflow
        self.expts = expts
        self.atmos_datam_dir = atmos_datam_dir
        self.atmos_dataw_dir = atmos_dataw_dir
        self.force = force

        self.all_tasks = []
        self.pending_tasks = []
        self.filename_task_map = {}
        self.working_tasks = []
        self.completed_tasks = []

    def get_next_pending(self):
        if self.pending_tasks:
            task = self.pending_tasks.pop(0)
            assert task.status == 'pending'
            task.status = 'working'
            self.working_tasks.append(task)
            logger.debug('get working task {}', task.index)
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
        logger.debug('updating task {} to {}', task_index, task_status)
        existing_task = self.all_tasks[task_index]
        existing_task.status = task_status
        if task_status == 'done':
            self.working_tasks.remove(existing_task)
            self.completed_tasks.append(existing_task)
            logger.debug('{} tasks completed', len(self.completed_tasks))

        for next_task in existing_task.next_tasks:
            if all([pt.status == 'done' for pt in next_task.prev_tasks]):
                next_task.status = 'pending'
                self.pending_tasks.append(next_task)
                logger.debug('adding pending task {}', next_task.index)

    def get_all_tasks(self):
        while True:
            # Will raise StopIteration when no more left.
            yield self.get_next_pending()

    def print_tasks(self):
        for task in self.all_tasks:
            print(task)

    def gen_tasks_for_analysis(self, analysis_name, analyser_cls):
        if self.run_type == 'cmd':
            for expt in self.expts:
                self._gen_cmd_tasks(analysis_name, analyser_cls)
        elif self.run_type == 'cycle':
            for expt in self.expts:
                self._gen_cycle_tasks(expt, analysis_name, analyser_cls)
        elif self.run_type == 'expt':
            for expt in self.expts:
                self._gen_expt_tasks(expt, analysis_name, analyser_cls)
        elif self.run_type == 'suite':
            self._gen_suite_tasks(analysis_name, analyser_cls)

    def gen_all_tasks(self):
        logger.debug('generating all tasks for {}', self.run_type)
        enabled_analysis = [a for a in self.analysis_workflow.values() if a[2]]
        self._scan_data_dirs(enabled_analysis)

        for analysis_name, analyser_cls, enabled in enabled_analysis:
            self.gen_tasks_for_analysis(analysis_name, analyser_cls)

        self._find_pending()
        logger.info('Generated {} tasks', len(self.all_tasks))

    def gen_single_analysis_tasks(self, analysis, filenames):
        logger.debug('generating single analysis tasks for {}', self.run_type)
        all_analysis = self.analysis_workflow.values()
        if filenames:
            self._find_filenames(filenames)
        else:
            self._scan_data_dirs(all_analysis)
        # N.B. ignores analysis enabled status.

        for analysis_name, analyser_cls, enabled in all_analysis:
            if analysis_name == analysis:
                self.gen_tasks_for_analysis(analysis_name, analyser_cls)

        self._find_pending()
        logger.info('Generated {} tasks', len(self.all_tasks))

    def _find_pending(self):
        for task in self.all_tasks:
            if all([pt.status == 'done' for pt in task.prev_tasks]):
                self.pending_tasks.append(task)

        logger.debug('{} pending tasks', len(self.pending_tasks))

    def _scan_data_dirs(self, analysis):
        self.all_filenames = []

        dirs_to_scan = []
        for expt in self.expts:
            datam_dir = self.atmos_datam_dir[expt]
            dataw_dir = self.atmos_dataw_dir[expt]
            dirs_to_scan.extend([datam_dir, dataw_dir])
            for analysis_name, analyser_cls, enabled in analysis:
                dirs_to_scan.append(analyser_cls.gen_output_dir(datam_dir))
                dirs_to_scan.append(analyser_cls.gen_output_dir(dataw_dir))

        # Ensure uniqueness.
        dirs_to_scan = set(dirs_to_scan)
        for dir in dirs_to_scan:
            logger.debug('Scanning dir: {}', dir)
            found_filenames = sorted(glob.glob(os.path.join(dir, '*')))
            self.all_filenames.extend(found_filenames)
        self.all_filenames = sorted(list(set(self.all_filenames)))

    def _find_filenames(self, filenames):
        self.all_filenames = []
        for filename in filenames:
            if not os.path.exists(filename):
                raise OmniumError('{} does not exist'.format(filename))
            self.all_filenames.append(os.path.abspath(filename))

    def _gen_single_file_tasks(self, expt, analyser_cls, analysis_name,
                               omnium_output_dir, data_type, done_filenames,
                               output_filename, delete, min_runid, max_runid):
        if not done_filenames:
            logger.debug('no files for {}', analyser_cls.analysis_name)
            return

        logger.debug('single file analysis')

        for filtered_filename in done_filenames:
            if output_filename:
                runid = 000
            else:
                runid, output_filename = analyser_cls.gen_output_filename(data_type,
                                                                          filtered_filename)
            if not (min_runid <= runid <= max_runid):
                logger.debug('file {} out of runid range: {} - {}',
                             filtered_filename, min_runid, max_runid)
                continue

            task = Task(len(self.all_tasks), expt, runid, self.run_type, 'analysis',
                        analyser_cls.analysis_name, analysis_name,
                        [filtered_filename], [os.path.join(omnium_output_dir, output_filename)])
            logger.debug(task)
            if filtered_filename in self.filename_task_map:
                prev_task = self.filename_task_map[filtered_filename]
                prev_task.add_next(task)
            for output_filename in task.output_filenames:
                self.filename_task_map[output_filename] = task
            self.all_tasks.append(task)
            # Don't fill up all_filenames if cmd.
            if self.run_type != 'cmd':
                # Check output filenames don't exist.
                for output_filename in task.output_filenames:
                    if os.path.exists(output_filename):
                        if not self.force:
                            msg = 'output file {} already exists'
                            logger.debug(msg, output_filename)
                        else:
                            msg = 'output file {} will be overwritten'
                            logger.debug(msg, output_filename)
                    else:
                        self.all_filenames.append(output_filename)
                        self.all_filenames.append(output_filename + '.done')

            if delete:
                logger.debug('will delete file: {}', filtered_filename)
                self.all_filenames.remove(filtered_filename)

    def _gen_multi_file_tasks(self, expt, analyser_cls, analysis_name,
                              omnium_output_dir, data_type, done_filenames,
                              output_filename, delete):
        assert not delete
        if not done_filenames:
            logger.debug('no files for {}', analyser_cls.analysis_name)
            return

        logger.debug('multi file analysis')

        if output_filename:
            runid = 0
        else:
            runid, output_filename = analyser_cls.gen_output_filename(data_type, done_filenames[0])

        task = Task(len(self.all_tasks), expt, runid, self.run_type, 'analysis',
                    analyser_cls.analysis_name, analysis_name,
                    done_filenames, [os.path.join(omnium_output_dir, output_filename)])
        for filtered_filename in done_filenames:
            if filtered_filename in self.filename_task_map:
                prev_task = self.filename_task_map[filtered_filename]
                prev_task.add_next(task)

        for output_filename in task.output_filenames:
            self.filename_task_map[output_filename] = task
        self.all_tasks.append(task)
        for output_filename in task.output_filenames:
            # Check output filenames don't exist.
            if os.path.exists(output_filename):
                if not self.force:
                    msg = 'output file {} already exists'
                    logger.debug(msg, output_filename)
                else:
                    msg = 'output file {} will be overwritten'
                    logger.debug(msg, output_filename)
            else:
                self.all_filenames.append(output_filename)
                self.all_filenames.append(output_filename + '.done')
        logger.debug(task)

    def _gen_cmd_tasks(self, analysis_name, analyser_cls):
        assert analyser_cls.single_file or analyser_cls.multi_file
        logger.debug('generating cmd tasks for {}', analyser_cls.analysis_name)

        data_type, filename_glob, filenames, output_filename, delete, min_runid, \
            max_runid = self._read_analysis_config(analysis_name)

        logger.debug('using files: {}', self.all_filenames)
        omnium_output_dir = os.path.dirname(self.all_filenames[0])

        if analyser_cls.single_file:
            self._gen_single_file_tasks(None, analyser_cls, analysis_name, omnium_output_dir,
                                        data_type, self.all_filenames, output_filename, delete,
                                        min_runid, max_runid)
        elif analyser_cls.multi_file:
            self._gen_multi_file_tasks(None, analyser_cls, analysis_name, omnium_output_dir,
                                       data_type, self.all_filenames, delete)

    def _gen_cycle_tasks(self, expt, analysis_name, analyser_cls):
        assert analyser_cls.single_file
        logger.debug('generating cycle tasks for {}', analyser_cls.analysis_name)
        data_type, filename_glob, filenames, output_filename, delete, min_runid, \
            max_runid = self._read_analysis_config(analysis_name)
        data_dir = self._get_data_dir(expt, data_type)
        delete = delete or analyser_cls.analysis_name == 'deleter'
        if filename_glob:
            # This is a little hacky: check both dirs.
            omnium_output_dir = analyser_cls.gen_output_dir(data_dir)
            filtered_filenames = sorted(fnmatch.filter(self.all_filenames,
                                                       os.path.join(data_dir, filename_glob)))
            filtered_filenames.extend(sorted(fnmatch.filter(self.all_filenames,
                                                            os.path.join(omnium_output_dir,
                                                                         filename_glob))))
        elif filenames:
            filtered_filenames = []
            for fn in filenames:
                fns = sorted(fnmatch.filter(self.all_filenames,
                                            os.path.join(data_dir, fn)))
                filtered_filenames.extend(fns)

        done_filenames = [fn for fn in filtered_filenames if fn + '.done' in self.all_filenames]
        logger.debug('found files: {}', done_filenames)

        self._gen_single_file_tasks(expt, analyser_cls, analysis_name, omnium_output_dir, data_type,
                                    done_filenames, output_filename, delete, min_runid, max_runid)

    def _gen_expt_tasks(self, expt, analysis_name, analyser_cls):
        assert analyser_cls.single_file or analyser_cls.multi_file
        logger.debug('generating expt tasks for {}', analyser_cls.analysis_name)
        data_type, filename_glob, filenames, output_filename, delete, min_runid, \
            max_runid = self._read_analysis_config(analysis_name)
        data_dir = self._get_data_dir(expt, data_type)
        omnium_output_dir = analyser_cls.gen_output_dir(data_dir)
        # This is a little hacky: check both dirs.
        logger.debug('using glob: {}', os.path.join(data_dir, filename_glob))
        filtered_filenames = sorted(fnmatch.filter(self.all_filenames,
                                                   os.path.join(data_dir, filename_glob)))
        filtered_filenames.extend(sorted(fnmatch.filter(self.all_filenames,
                                                        os.path.join(omnium_output_dir,
                                                                     filename_glob))))
        logger.debug('using glob: {}', os.path.join(omnium_output_dir, filename_glob))
        done_filenames = [fn for fn in filtered_filenames if fn + '.done' in self.all_filenames]
        logger.debug('found files: {}', done_filenames)

        if analyser_cls.single_file:
            self._gen_single_file_tasks(expt, analyser_cls, analysis_name, omnium_output_dir,
                                        data_type, done_filenames, output_filename, delete,
                                        min_runid, max_runid)
        elif analyser_cls.multi_file:
            self._gen_multi_file_tasks(expt, analyser_cls, analysis_name, omnium_output_dir,
                                       data_type, done_filenames, output_filename, delete)

    def _gen_suite_tasks(self, analysis_name, analyser_cls):
        logger.debug('generating suite tasks for {}', analyser_cls.analysis_name)
        assert analyser_cls.multi_expt
        filenames = []
        for expt in self.expts:
            data_type, filename_glob, filenames, output_filename, delete, min_runid, \
                max_runid = self._read_analysis_config(analysis_name)
            data_dir = self._get_data_dir(expt, data_type)
            filtered_filenames = sorted(fnmatch.filter(self.all_filenames,
                                                       os.path.join(data_dir, filename_glob)))
            done_filenames = [fn for fn in filtered_filenames if fn + '.done' in self.all_filenames]
            logger.debug('found files: {}', done_filenames)
            assert len(done_filenames) <= 1
            if done_filenames:
                filenames.append(done_filenames[0])

        if not filenames:
            logger.debug('found no files for {}', analysis_name)
            return

        assert len(filenames) == len(self.expts)

        res_dir = os.path.join(self.suite.suite_dir, 'share/data/history/suite_output')
        if output_filename:
            runid = 0
        else:
            runid, output_filename = analyser_cls.gen_output_filename(data_type, filenames[0])
        task = Task(len(self.all_tasks), self.expts, runid, 'suite', 'analysis',
                    analyser_cls.analysis_name, analysis_name,
                    filenames, [os.path.join(res_dir, output_filename)])

        # TODO: how to handle deps for suite tasks?
        for filename in filenames:
            if filename in self.filename_task_map:
                prev_task = self.filename_task_map[filename]
                prev_task.add_next(task)

        for output_filename in task.output_filenames:
            self.filename_task_map[output_filename] = task

        self.all_tasks.append(task)
        self.all_filenames.extend(task.output_filenames)
        self.all_filenames.extend([fn + '.done' for fn in task.output_filenames])

    def _get_data_dir(self, expt, data_type):
        if data_type == 'datam':
            data_dir = self.atmos_datam_dir[expt]
        elif data_type == 'dataw':
            data_dir = self.atmos_dataw_dir[expt]
        logger.debug('using data_dir: {}', data_dir)
        return data_dir

    def _obs_read_analysis_config(self, analysis_name):
        # TODO: delete.
        analysis_config = self.config[analysis_name]
        data_type = analysis_config['data_type']
        analysis_config = self.config[analysis_name]
        filename_glob = analysis_config.get('filename', None)
        filenames = analysis_config.get('filenames', None)
        if filename_glob is None and filenames is None:
            raise OmniumError('One of filename_glob or filenames must be set')
        output_filename = analysis_config.get('output_filename', None)
        delete = analysis_config.getboolean('delete', False)
        min_runid = analysis_config.getint('min_runid', 0)
        max_runid = analysis_config.getint('max_runid', int(1e10))

        logger.debug('using filename_glob: {}', filename_glob)
        return data_type, filename_glob, filenames, output_filename, delete, min_runid, max_runid
