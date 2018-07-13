from unittest import TestCase

from mock import Mock, patch, call

from omnium.run_control import Task, TaskMaster
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
            'basic': [self.suite, 'cmd', self.settings, True],
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
        task_master.pending_tasks = [task]
        with self.assertRaises(AssertionError):
            task_master.get_next_pending()

    def test_get_next_pending4(self):
        task_master = TaskMaster(*self.suite_args['basic'])
        task = Mock()
        task.status = 'pending'
        task_master.pending_tasks = [task]
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
        assert task1.status == 'pending' and task1 in task_master.pending_tasks
        assert task2.status == 'pending' and task2 in task_master.pending_tasks

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
        analyser_cls = Mock()

        task_master._run_type = 'cmd'
        task_master.gen_tasks_for_analysis(analyser_cls)
        mock_gen_cmd.assert_has_calls([call(analyser_cls)])

    @patch('omnium.TaskMaster.gen_cycle_tasks')
    def test_gen_tasks_for_analysis2(self, mock_gen_cycle):
        task_master = TaskMaster(*self.suite_args['basic'])
        task_master._expts = ['expt1', 'expt2']
        analyser_cls = Mock()
        task_master._run_type = 'cycle'
        task_master.gen_tasks_for_analysis(analyser_cls)
        mock_gen_cycle.assert_has_calls([call('expt1', analyser_cls),
                                         call('expt2', analyser_cls)])

    @patch('omnium.TaskMaster.gen_expt_tasks')
    def test_gen_tasks_for_analysis3(self, mock_gen_expt):
        task_master = TaskMaster(*self.suite_args['basic'])
        task_master._expts = ['expt1', 'expt2']
        analyser_cls = Mock()
        task_master._run_type = 'expt'
        task_master.gen_tasks_for_analysis(analyser_cls)
        mock_gen_expt.assert_has_calls([call('expt1', analyser_cls),
                                        call('expt2', analyser_cls)])

    @patch('omnium.TaskMaster.gen_suite_tasks')
    def test_gen_tasks_for_analysis4(self, mock_gen_suite):
        task_master = TaskMaster(*self.suite_args['basic'])
        task_master._expts = ['expt1', 'expt2']
        analyser_cls = Mock()
        task_master._run_type = 'suite'
        task_master.gen_tasks_for_analysis(analyser_cls)
        mock_gen_suite.assert_has_calls([call(analyser_cls)])

    @patch('omnium.TaskMaster.gen_tasks_for_analysis')
    def test_gen_all_tasks(self, mock_gen):
        task_master = TaskMaster(*self.suite_args['basic'])
        task_master._expts = ['expt1', 'expt2']

        analyser_cls = Mock()

        enabled_analysis = [
            ('mock_analysis1', analyser_cls, True),
        ]
        task_master.gen_all_tasks(['e0', 'e1'], [], enabled_analysis)
        mock_gen.assert_called_with(analyser_cls)

    @patch('omnium.TaskMaster.gen_tasks_for_analysis')
    def test_single_analysis_task(self, mock_gen):
        task_master = TaskMaster(*self.suite_args['basic'])
        task_master._expts = ['expt1', 'expt2']

        analyser_cls1 = Mock()
        analyser_cls2 = Mock()
        all_analysis = [
            ('mock_analysis1', analyser_cls1, True),
            ('mock_analysis2', analyser_cls2, False),
        ]

        self.analysis_workflow.values.return_value = all_analysis
        expts = ['e1', 'e2']

        task_master.gen_single_analysis_tasks(expts, [], self.analysis_workflow, 'mock_analysis2')
        mock_gen.assert_called_with(analyser_cls2)

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
        assert task1 in task_master.pending_tasks
        assert task2 in task_master.pending_tasks
        assert task3 not in task_master.pending_tasks
        assert task4 not in task_master.pending_tasks
