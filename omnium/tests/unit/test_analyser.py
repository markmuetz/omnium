from unittest import TestCase

from mock import Mock, patch, mock_open
from omnium import OmniumError
from omnium.analyser import Analyser
from omnium.task import Task
from omnium.setup_logging import setup_logger

setup_logger()

task = Task(0, ['S0'], None, 'suite', 'analysis', 'dummy_analysis',
            ['fn1'], ['fn1.dummy_analysis.nc'])
task_single_expt = Task(0, 'S0', None, 'suite', 'analysis', 'dummy_analysis',
                        ['fn1'], ['fn1.dummy_analysis.nc'])
multi_expt_task = Task(0, ['S0', 'S1'], None, 'suite', 'analysis',
                       'dummy_analysis',
                       ['fn1', 'fn1'], ['fn1.dummy_analysis.nc'])


class TestAnalyserInstanceCreation(TestCase):
    def setUp(self):
        setup_logger()

    def test_abstract(self):
        with self.assertRaises(TypeError):
            Analyser()

    def test_not_fully_implemented(self):
        class BrokenAnalyser(Analyser):
            # Haven't overridden load/run/save.
            pass

        with self.assertRaises(TypeError):
            BrokenAnalyser()

    def test_no_name(self):
        class BrokenAnalyser2(Analyser):
            # Haven't analysis_name
            def load(self):
                pass

            def run(self):
                pass

            def save(self, state, suite):
                pass

        with self.assertRaises(AssertionError):
            BrokenAnalyser2(None, task, None)

    def test_both_multi(self):
        class BrokenAnalyser2(Analyser):
            analysis_name = 'working_analyser'
            multi_expt = True
            multi_file = True

            def load(self):
                pass

            def run(self):
                pass

            def save(self, state, suite):
                pass

        with self.assertRaises(AssertionError):
            BrokenAnalyser2(None, task, None)

    def test_ctor(self):
        class WorkingAnalyser(Analyser):
            analysis_name = 'working_analyser'
            single_file = True
            input_dir = '/input/dir'
            input_filename = 'file.name'
            output_dir = '/output/dir'
            output_filenames = ['out.file.name']
            settings = ''

            def load(self):
                pass

            def run(self):
                pass

            def save(self, state, suite):
                pass

        patcher = patch('os.makedirs')
        patcher.start()
        suite = Mock()
        suite.check_filename_missing = lambda x: False
        wa = WorkingAnalyser(suite, task, None)
        assert not wa.multi_expt
        assert not wa.multi_file
        patcher.stop()


class SingleAnalyser(Analyser):
    analysis_name = 'working_analyser'
    single_file = True
    input_dir = '/input/dir'
    input_filename = 'file.name'
    output_dir = '/output/dir'
    output_filenames = ['out.file.name']

    def load(self):
        self.load_cubes()

    def run(self):
        pass

    def save(self, state, suite):
        pass


class MultiExptAnalyser(Analyser):
    analysis_name = 'working_analyser'
    multi_expt = True
    input_dir = '/input/dir'
    input_filename = 'file.name'
    output_dir = '/output/dir'
    output_filenames = ['out.file.name']

    def load(self):
        self.load_cubes()

    def run(self):
        pass

    def save(self, state, suite):
        pass


class MultiFileAnalyser(Analyser):
    analysis_name = 'working_analyser'
    multi_file = True
    input_dir = '/input/dir'
    input_filename = 'file.name'
    output_dir = '/output/dir'
    output_filenames = ['out.file.name']

    def load(self):
        self.load_cubes()

    def run(self):
        pass

    def save(self, state, suite):
        pass


class TestAnalyserInstanceSetup(TestCase):
    def setUp(self):
        self.patcher = patch('os.makedirs')
        self.patcher.start()
        self.suite = Mock()
        self.settings = Mock()
        self.suite.check_filename_missing = lambda x: False
        setup_logger()

    def tearDown(self):
        self.patcher.stop()

    def test_ctor_single(self):
        wa = SingleAnalyser(self.suite, task, self.settings)
        assert not wa.multi_expt
        assert not wa.multi_file

    def test_ctor_single_dump(self):
        wa = SingleAnalyser(self.suite, task, self.settings)
        assert not wa.multi_expt
        assert not wa.multi_file

    def test_ctor_multi_expt(self):
        mea = MultiExptAnalyser(self.suite, task, self.settings)
        assert mea.multi_expt
        assert not mea.multi_file

    def test_ctor_multi_file(self):
        mfa = MultiFileAnalyser(self.suite, task, self.settings)
        assert not mfa.multi_expt
        assert mfa.multi_file

    def test_ctor_multi_file_dump(self):
        mfa = MultiFileAnalyser(self.suite, task, self.settings)
        assert not mfa.multi_expt
        assert mfa.multi_file


class TestAnalyserInstanceFunction(TestCase):
    def setUp(self):
        self.mock_make_dirs = patch('os.makedirs')
        self.mock_make_dirs.start()

        self.mock_log_file = patch('builtins.open', mock_open())
        self.mock_log_file.start()

        self.suite = Mock()
        self.settings = Mock()
        self.suite.check_filename_missing = lambda x: False

        setup_logger()

    def tearDown(self):
        self.mock_make_dirs.stop()
        self.mock_log_file.stop()

    def test_already_analysed(self):
        wa = SingleAnalyser(self.suite, task, self.settings)
        patcher = patch('os.path.exists')
        exists = patcher.start()
        exists.side_effect = lambda x: True
        assert wa.already_analysed()
        patcher.stop()

    def test_append_log(self):
        wa = SingleAnalyser(self.suite, task, self.settings)
        wa.append_log('test')

    @patch('iris.load')
    def test_load_cubes_single(self, mock_load):
        sa = SingleAnalyser(self.suite, task, self.settings)
        mock_load.return_value = ['fn.nc']
        sa.load()
        assert sa.cubes == ['fn.nc']

    def test_load_single_missing(self):
        sa = SingleAnalyser(self.suite, task, self.settings)

        def abort_if_missing(fn):
            raise OmniumError('missing')

        self.suite.abort_if_missing = abort_if_missing
        with self.assertRaises(OmniumError):
            sa.load()

    @patch('iris.load')
    def test_load_multi_expt(self, mock_load):
        mea = MultiExptAnalyser(self.suite, multi_expt_task, self.settings)
        filename = 'atmos.000.pp1.nc'
        mock_load.return_value = [filename]
        mea.load()
        assert mea.expt_cubes['S0'] == [filename]
        assert mea.expt_cubes['S1'] == [filename]

    def test_load_multi_expt_missing(self):
        mea = MultiExptAnalyser(self.suite, multi_expt_task, self.settings)

        def abort_if_missing(fn):
            raise OmniumError('missing')

        self.suite.abort_if_missing = abort_if_missing
        with self.assertRaises(OmniumError):
            mea.load()

    @patch('iris.load')
    @patch('iris.cube.CubeList.concatenate')
    def test_load_multi_file(self, mock_concatenate, mock_load):
        mfa = MultiFileAnalyser(self.suite, task, self.settings)
        mock_concatenate.return_value = mfa.task.filenames
        mfa.load()
        print(mfa.cubes)
        print(mfa.task.filenames)
        assert mfa.cubes == mfa.task.filenames

    def test_load_multi_file_missing(self):
        mfa = MultiFileAnalyser(self.suite, task, self.settings)

        def abort_if_missing(fn):
            raise OmniumError('missing')

        self.suite.abort_if_missing = abort_if_missing
        with self.assertRaises(OmniumError):
            mfa.load()

    @patch.object(SingleAnalyser, 'run')
    def test_run(self, mock_run):
        sa = SingleAnalyser(self.suite, task, self.settings)
        sa.analysis_run()
        mock_run.assert_called_with()

    @patch('iris.cube.CubeList')
    @patch('iris.save')
    def test_save_results_cube(self, mock_save, mock_CubeList):
        sa = SingleAnalyser(self.suite, task, self.settings)
        sa.save_results_cubes(None, self.suite)
        mock_CubeList.assert_called_with([])
        mock_save.assert_not_called()
        self.suite.analysis_hash = [b'a' * 64, b'b' * 64]
        self.suite.analysis_status = ['clean', 'clean']

        results = [('result_{}'.format(i), Mock(attributes={'omnium_cube_id': i}))
                   for i in range(5)]
        for name, result in results:
            sa.results[name] = result
        mock_CubeList.return_value = [r[1] for r in results]
        sa.save_results_cubes(None, self.suite)
        mock_CubeList.assert_called_with(list(sa.results.values()))
        mock_save.assert_called()

    def test_display_results(self):
        sa = SingleAnalyser(self.suite, task, self.settings)

        sa.display_results = Mock()
        sa.analysis_display()
        sa.display_results.assert_called_with()

    @patch.object(Analyser, 'file_path')
    def test_save_text(self, mock_file_path):
        sa = SingleAnalyser(self.suite, task, self.settings)
        mock_file_path.return_value = 'filename'
        with patch('builtins.open', mock_open()) as mock_file:
            sa.save_text('name', 'message')
            mock_file.assert_called_with(*('filename', 'w'))
            handle = mock_file()
            args, kwargs = handle.write.call_args
            assert args[0] == 'message'

    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_figpath(self, mock_makedirs, mock_exists):
        sa = SingleAnalyser(self.suite, task_single_expt, self.settings)

        mock_exists.return_value = False
        sa.file_path('steve')
        mock_makedirs.assert_called()
        mock_makedirs.reset_mock()

        mock_exists.return_value = True
        sa.file_path('steve')
        mock_makedirs.assert_not_called()
        mock_makedirs.reset_mock()

        sa.multi_expt = True
        sa.file_path('steve')
