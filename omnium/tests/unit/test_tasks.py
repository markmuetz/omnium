from unittest import TestCase

from mock import Mock, patch, call

from omnium import OmniumError
from omnium.task import Task, TaskMaster
from omnium.setup_logging import setup_logger


class TestTask(TestCase):
    def test_task_init(self):
        t0 = Task(0, 'S0', None, 'cycle', 'analysis', 'cloud_analysis',
                  ['atmos.pp1.nc'], ['atmos.cloud_analysis.nc'])
        repr(t0)

    def test_task_init_suite(self):
        t0 = Task(0, 'S0', None, 'suite', 'analysis', 'cloud_analysis',
                  ['atmos.pp1.nc'], ['atmos.cloud_analysis.nc'])
        repr(t0)

    def test_task_chain(self):
        t0 = Task(0, 'S0', None, 'suite', 'analysis', 'cloud_analysis',
                  ['atmos.pp1.nc'], ['atmos.cloud_analysis.nc'])
        t1 = Task(1, 'S0', None, 'cycle', 'analysis', 'cloud_analysis',
                  ['atmos.pp1.nc'], ['atmos.cloud_analysis.nc'])
        t0.add_next(t1)
        assert t1 in t0.next_tasks
        assert t0 in t1.prev_tasks


class TestTaskMaster(TestCase):
    def setUp(self):
        self.suite = Mock()
        self.analysis_workflow = Mock()
        self.settings = Mock()
        self.suite_args = {
            'basic': [self.suite, 'cmd', self.analysis_workflow, ['expt1'], self.settings, True],
        }
        setup_logger()

    def test_task_master_init(self):
        task_master = TaskMaster(*self.suite_args['basic'])

    def test_get_next_pending1(self):
        task_master = TaskMaster(*self.suite_args['basic'])
        with self.assertRaises(StopIteration):
            task_master.get_next_pending()

    def test_get_next_pending2(self):
        task_master = TaskMaster(*self.suite_args['basic'])
        task_master.all_tasks = [Mock()]
        assert task_master.get_next_pending() is None

    def test_get_next_pending3(self):
        task_master = TaskMaster(*self.suite_args['basic'])
        task = Mock()
        task.status = 'working'
        task_master._pending_tasks = [task]
        with self.assertRaises(AssertionError):
            task_master.get_next_pending()

    def test_get_next_pending4(self):
        task_master = TaskMaster(*self.suite_args['basic'])
        task = Mock()
        task.status = 'pending'
        task_master._pending_tasks = [task]
        assert task_master.get_next_pending() is task
        assert task.status == 'working'

    def test_update_task1(self):
        task_master = TaskMaster(*self.suite_args['basic'])
        task = Mock()
        task.status = 'pending'
        task.next_tasks = []
        task_master.all_tasks = [task]
        task_master.update_task(0, 'working')
        assert task.status == 'working'

    def test_update_task2(self):
        task_master = TaskMaster(*self.suite_args['basic'])
        task = Mock()
        task1 = Mock()
        task2 = Mock()
        task1.prev_tasks = [task]
        task2.prev_tasks = [task]
        task.status = 'working'
        task_master._working_tasks = [task]
        task.next_tasks = [task1, task2]
        task_master.all_tasks = [task]
        task_master.update_task(0, 'done')
        assert task.status == 'done'
        assert task1.status == 'pending' and task1 in task_master._pending_tasks
        assert task2.status == 'pending' and task2 in task_master._pending_tasks

    @patch('omnium.TaskMaster.get_next_pending')
    def test_get_all_tasks1(self, mock_get_next_pending):
        task_master = TaskMaster(*self.suite_args['basic'])
        task = Mock()
        mock_get_next_pending.return_value = task
        rtask = next(task_master.get_all_tasks())
        assert task == rtask

    @patch('omnium.TaskMaster.get_next_pending')
    def test_get_all_tasks2(self, mock_get_next_pending):
        task_master = TaskMaster(*self.suite_args['basic'])

        def r():
            raise StopIteration

        mock_get_next_pending.side_effect = r

        with self.assertRaises(StopIteration):
            next(task_master.get_all_tasks())

    @patch('builtins.print')
    def test_print_tasks(self, mock_print):
        task_master = TaskMaster(*self.suite_args['basic'])
        task = Mock()
        task_master.all_tasks = [task]
        task_master.print_tasks()
        mock_print.assert_called_with(task)

    @patch('omnium.TaskMaster.gen_cmd_tasks')
    def test_gen_tasks_for_analysis1(self, mock_gen_cmd):
        task_master = TaskMaster(*self.suite_args['basic'])
        task_master._expts = ['expt1', 'expt2']
        analysis_class = Mock()

        task_master._run_type = 'cmd'
        task_master.gen_tasks_for_analysis(analysis_class)
        mock_gen_cmd.assert_has_calls([call(analysis_class),
                                       call(analysis_class)])

    @patch('omnium.TaskMaster.gen_cycle_tasks')
    def test_gen_tasks_for_analysis2(self, mock_gen_cycle):
        task_master = TaskMaster(*self.suite_args['basic'])
        task_master._expts = ['expt1', 'expt2']
        analysis_class = Mock()
        task_master._run_type = 'cycle'
        task_master.gen_tasks_for_analysis(analysis_class)
        mock_gen_cycle.assert_has_calls([call('expt1', analysis_class),
                                         call('expt2', analysis_class)])

    @patch('omnium.TaskMaster.gen_expt_tasks')
    def test_gen_tasks_for_analysis3(self, mock_gen_expt):
        task_master = TaskMaster(*self.suite_args['basic'])
        task_master._expts = ['expt1', 'expt2']
        analysis_class = Mock()
        task_master._run_type = 'expt'
        task_master.gen_tasks_for_analysis(analysis_class)
        mock_gen_expt.assert_has_calls([call('expt1', analysis_class),
                                        call('expt2', analysis_class)])

    @patch('omnium.TaskMaster.gen_suite_tasks')
    def test_gen_tasks_for_analysis4(self, mock_gen_suite):
        task_master = TaskMaster(*self.suite_args['basic'])
        task_master._expts = ['expt1', 'expt2']
        analysis_class = Mock()
        task_master._run_type = 'suite'
        task_master.gen_tasks_for_analysis(analysis_class)
        mock_gen_suite.assert_has_calls([call(analysis_class)])

    @patch('omnium.TaskMaster.gen_tasks_for_analysis')
    @patch('omnium.TaskMaster._scan_data_dirs')
    def test_gen_all_tasks(self, mock_scan, mock_gen):
        task_master = TaskMaster(*self.suite_args['basic'])
        task_master._expts = ['expt1', 'expt2']
        task_master._analysis_workflow = Mock()

        analysis_class1 = Mock()
        analysis_class2 = Mock()

        task_master._analysis_workflow.values.return_value = [
            ('mock_analysis1', analysis_class1, True),
            ('mock_analysis2', analysis_class2, False),
        ]
        task_master.gen_all_tasks()
        mock_scan.assert_called_with([('mock_analysis1', analysis_class1, True)])
        mock_gen.assert_called_with(analysis_class1)

    @patch('omnium.TaskMaster.gen_tasks_for_analysis')
    @patch('omnium.TaskMaster._find_filenames')
    @patch('omnium.TaskMaster._scan_data_dirs')
    def test_single_analysis_task(self, mock_scan, mock_find, mock_gen):
        task_master = TaskMaster(*self.suite_args['basic'])
        task_master._expts = ['expt1', 'expt2']
        task_master._analysis_workflow = Mock()

        analysis_class1 = Mock()
        analysis_class2 = Mock()
        all_analysis = [
            ('mock_analysis1', analysis_class1, True),
            ('mock_analysis2', analysis_class2, False),
        ]

        task_master._analysis_workflow.values.return_value = all_analysis

        task_master.gen_single_analysis_tasks('mock_analysis2', [])
        mock_gen.assert_called_with(analysis_class2)
        mock_scan.assert_called_with(all_analysis)

        task_master.gen_single_analysis_tasks('mock_analysis2', ['fn'])
        mock_find.assert_called_with(['fn'])

    def test_find_pending(self):
        task_master = TaskMaster(*self.suite_args['basic'])
        task1 = Mock()
        task2 = Mock()
        task3 = Mock()
        task4 = Mock()
        task1.prev_tasks = []
        task2.prev_tasks = []
        task3.prev_tasks = [task1]
        task4.prev_tasks = [task1, task2]
        task1.status = 'pending'
        task2.status = 'pending'
        task1.next_tasks = [task3, task4]
        task2.next_tasks = [task4]
        task_master.all_tasks = [task1, task2, task3, task4]
        task_master._find_pending()
        assert task1 in task_master._pending_tasks
        assert task2 in task_master._pending_tasks
        assert task3 not in task_master._pending_tasks
        assert task4 not in task_master._pending_tasks

    @patch('omnium.task.TaskMaster._get_package_version')
    @patch('glob.glob')
    def test_scan_dirs_empty(self, mock_glob, mock_get_package_version):
        task_master = TaskMaster(*self.suite_args['basic'])
        mock_analysis_cls = Mock()
        mock_analysis_cls.input_dir.format.return_value = '/mock_dir'

        mock_settings = Mock()
        mock_settings.get_hash.return_value = 'abcdefghijklmnop'
        mock_settings.package = Mock()
        self.suite.analysers.get_settings.return_value = mock_settings.package, mock_settings
        mock_get_package_version.return_value = 'pkg_name_v_-99'
        analysis = [('mock_analysis', mock_analysis_cls, True)]

        self.suite.suite_dir = 'suite_dir'

        mock_glob.return_value = []
        task_master._scan_data_dirs(analysis)
        assert task_master.virtual_dir == []

    @patch('omnium.task.TaskMaster._get_package_version')
    @patch('glob.glob')
    def test_scan_dirs_finds_some(self, mock_glob, mock_get_package_version):
        task_master = TaskMaster(*self.suite_args['basic'])
        mock_analysis_cls = Mock()
        mock_analysis_cls.input_dir.format.return_value = '/mock_dir'

        mock_settings = Mock()
        mock_settings.get_hash.return_value = 'abcdefghijklmnop'
        mock_settings.package = Mock()
        self.suite.analysers.get_settings.return_value = mock_settings.package, mock_settings
        mock_get_package_version.return_value = 'pkg_name_v_-99'

        analysis = [('mock_analysis', mock_analysis_cls, True)]
        mock_analysis_cls.gen_output_dir = lambda x: x + '/mock_analysis_dir'
        fns = ['fn1', 'fn2']

        def mock_glob_fn(arg):
            print(arg)
            return fns

        self.suite.suite_dir = 'suite_dir'

        mock_glob.side_effect = mock_glob_fn
        task_master._scan_data_dirs(analysis)
        assert mock_glob.call_count == 1
        assert task_master.virtual_dir == fns

    @patch('os.path.exists')
    @patch('os.path.abspath')
    def test_find_filenames(self, mock_abspath, mock_exists):
        task_master = TaskMaster(*self.suite_args['basic'])

        def mock_exists_fn(fn):
            return True

        mock_exists.side_effect = mock_exists_fn
        mock_abspath.side_effect = lambda x: '/' + x
        fns = ['fn1', 'fn2']
        task_master._find_filenames(fns)
        output_fns = ['/' + f for f in fns]
        assert(set(task_master.virtual_dir) == set(output_fns))

    @patch('os.path.exists')
    @patch('os.path.abspath')
    def test_find_filenames_no_done(self, mock_abspath, mock_exists):
        task_master = TaskMaster(*self.suite_args['basic'])

        def mock_exists_fn(fn):
            return fn[-5:] != '.done'

        mock_exists.side_effect = mock_exists_fn
        mock_abspath.side_effect = lambda x: '/' + x
        fns = ['fn1', 'fn2']
        task_master._find_filenames(fns)
        output_fns = ['/' + f for f in fns]
        assert(set(task_master.virtual_dir) == set(output_fns))

    @patch('os.path.exists')
    @patch('os.path.abspath')
    def test_find_filenames_not_there(self, mock_abspath, mock_exists):
        task_master = TaskMaster(*self.suite_args['basic'])

        def mock_exists_fn(fn):
            return False

        mock_exists.side_effect = mock_exists_fn
        mock_abspath.side_effect = lambda x: '/' + x
        fns = ['fn1', 'fn2']
        with self.assertRaises(OmniumError):
            task_master._find_filenames(fns)
