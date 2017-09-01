from unittest import TestCase
from mock import Mock, patch, mock_open
from configparser import ConfigParser

from omnium.analyzer import Analyzer
from omnium import OmniumError


class TestAnalyzerInstanceCreation(TestCase):
    def test_abstract(self):
        with self.assertRaises(TypeError):
            Analyzer()

    def test_not_fully_implemented(self):
        class BrokenAnalyser(Analyzer):
            # Haven't overridden run_analysis.
            pass

        with self.assertRaises(TypeError):
            BrokenAnalyser()

    def test_no_name(self):
        class BrokenAnalyser2(Analyzer):
            # Haven't analysis_name
            def run_analysis(self):
                pass

        with self.assertRaises(AttributeError):
            BrokenAnalyser2(None, 'datam', {'expt': '/path/to/data_dir'}, '',
                            ['atmos.000.pp1.nc'], ['expt'])

    def test_both_multi(self):
        class BrokenAnalyser2(Analyzer):
            analysis_name = 'working_analyser'
            multi_expt = True
            multi_file = True

            # Haven't analysis_name
            def run_analysis(self):
                pass

        with self.assertRaises(OmniumError):
            BrokenAnalyser2(None, 'datam', {'expt': '/path/to/data_dir'}, '',
                            ['atmos.000.pp1.nc'], ['expt'])

    def test_ctor(self):
        class WorkingAnalyser(Analyzer):
            analysis_name = 'working_analyser'

            def run_analysis(self):
                pass

        patcher = patch('os.makedirs')
        patcher.start()
        suite = Mock()
        suite.check_filename_missing = lambda x: False
        wa = WorkingAnalyser(suite, 'datam', {'expt': '/path/to/data_dir'}, '',
                             ['atmos.000.pp1.nc'], ['expt'])
        assert not wa.multi_expt
        assert not wa.multi_file
        patcher.stop()


class SingleAnalyser(Analyzer):
    analysis_name = 'working_analyser'

    def run_analysis(self):
        pass


class MultiExptAnalyser(Analyzer):
    analysis_name = 'working_analyser'
    multi_expt = True

    def run_analysis(self):
        pass


class MultiFileAnalyser(Analyzer):
    analysis_name = 'working_analyser'
    multi_file = True

    def run_analysis(self):
        pass


class TestAnalyzerInstanceSetup(TestCase):
    def setUp(self):
        self.patcher = patch('os.makedirs')
        self.patcher.start()
        self.suite = Mock()
        self.suite.check_filename_missing = lambda x: False

    def tearDown(self):
        self.patcher.stop()

    def test_ctor_single(self):
        wa = SingleAnalyser(self.suite, 'datam', {'expt': '/path/to/data_dir'}, '',
                            ['atmos.000.pp1.nc'], ['expt'])
        assert not wa.multi_expt
        assert not wa.multi_file

    def test_ctor_single_dump(self):
        wa = SingleAnalyser(self.suite, 'datam', {'expt': '/path/to/data_dir'}, '',
                            ['atmos_da000.nc'], ['expt'])
        assert not wa.multi_expt
        assert not wa.multi_file

    def test_ctor_multi_expt(self):
        mea = MultiExptAnalyser(self.suite, 'datam', {'expt': '/path/to/data_dir'}, '',
                                ['atmos.000.pp1.nc'], ['expt'])
        assert mea.multi_expt
        assert not mea.multi_file

    def test_ctor_multi_file(self):
        mfa = MultiFileAnalyser(self.suite, 'datam', {'expt': '/path/to/data_dir'}, '',
                                ['atmos.000.pp1.nc'], ['expt'])
        assert not mfa.multi_expt
        assert mfa.multi_file

    def test_ctor_multi_file_dump(self):
        mfa = MultiFileAnalyser(self.suite, 'datam', {'expt': '/path/to/data_dir'}, '',
                                ['atmos_da000.nc'], ['expt'])
        assert not mfa.multi_expt
        assert mfa.multi_file

    def test_set_config(self):
        wa = SingleAnalyser(self.suite, 'datam', {'expt': '/path/to/data_dir'}, '',
                            ['atmos.000.pp1.nc'], ['expt'])
        config = ConfigParser()
        config.add_section('config')
        config.set('config', 'c1', '1')
        config.set('config', 'c2', 'two')
        config.set('config', 'force', 'True')
        wa.set_config(config['config'])
        assert wa._config['c1'] == '1'
        assert wa._config['c2'] == 'two'
        assert wa.force


class TestAnalyzerInstanceFunction(TestCase):
    def setUp(self):
        self.patcher = patch('os.makedirs')
        self.patcher.start()
        self.suite = Mock()
        self.suite.check_filename_missing = lambda x: False

    def tearDown(self):
        self.patcher.stop()

    def test_already_analysed(self):
        wa = SingleAnalyser(self.suite, 'datam', {'expt': '/path/to/data_dir'}, '',
                            ['atmos.000.pp1.nc'], ['expt'])
        patcher = patch('os.path.exists')
        exists = patcher.start()
        exists.side_effect = lambda x: True
        assert wa.already_analyzed()
        patcher.stop()

    def test_append_log(self):
        wa = SingleAnalyser(self.suite, 'datam', {'expt': '/path/to/data_dir'}, '',
                            ['atmos.000.pp1.nc'], ['expt'])
        with patch('__builtin__.open', mock_open()) as mock_file:
            wa.append_log('test')
            mock_file.assert_called_with(*(wa.logname, 'a'))
            handle = mock_file()
            args, kwargs = handle.write.call_args
            assert args[0][-5:] == 'test\n'

    @patch('iris.load')
    def test_load_single(self, mock_load):
        wa = SingleAnalyser(self.suite, 'datam', {'expt': '/path/to/data_dir'}, '',
                            ['atmos.000.pp1.nc'], ['expt'])
        mock_load.return_value = [wa.filename]
        wa.load()
        assert wa.cubes == [wa.filename]

    def test_load_single_missing(self):
        wa = SingleAnalyser(self.suite, 'datam', {'expt': '/path/to/data_dir'}, '',
                            ['atmos.000.pp1.nc'], ['expt'])

        def abort_if_missing(fn):
            raise OmniumError('missing')

        self.suite.abort_if_missing = abort_if_missing
        with self.assertRaises(OmniumError):
            wa.load()

    @patch('iris.load')
    def test_load_multi_expt(self, mock_load):
        mea = MultiExptAnalyser(self.suite, 'datam',
                                {'expt1': '/path/to/data_dir', 'expt2': '/path/to/data_dir'}, '',
                                ['atmos.000.pp1.nc'], ['expt1', 'expt2'])
        filename = 'atmos.000.pp1.nc'
        mock_load.return_value = [filename]
        mea.load()
        assert mea.expt_cubes['expt1'] == [filename]
        assert mea.expt_cubes['expt2'] == [filename]

    def test_load_multi_expt_missing(self):
        mea = MultiExptAnalyser(self.suite, 'datam',
                                {'expt1': '/path/to/data_dir', 'expt2': '/path/to/data_dir'}, '',
                                ['atmos.000.pp1.nc'], ['expt1', 'expt2'])

        def abort_if_missing(fn):
            raise OmniumError('missing')

        self.suite.abort_if_missing = abort_if_missing
        with self.assertRaises(OmniumError):
            mea.load()

    @patch('iris.load')
    def test_load_multi_file(self, mock_load):
        mfa = MultiFileAnalyser(self.suite, 'datam', {'expt': '/path/to/data_dir'}, '',
                                ['atmos.000.pp1.nc'], ['expt'])
        mock_load.return_value = mfa.filenames
        mfa.load()
        assert mfa.cubes == mfa.filenames

    def test_load_multi_file_missing(self):
        mfa = MultiFileAnalyser(self.suite, 'datam', {'expt': '/path/to/data_dir'}, '',
                                ['atmos.000.pp1.nc'], ['expt'])

        def abort_if_missing(fn):
            raise OmniumError('missing')

        self.suite.abort_if_missing = abort_if_missing
        with self.assertRaises(OmniumError):
            mfa.load()

    @patch('os.path.exists')
    @patch('iris.load')
    def test_load_results(self, mock_load, mock_exists):
        mock_exists.return_value = True
        wa = SingleAnalyser(self.suite, 'datam', {'expt': '/path/to/data_dir'}, '',
                            ['atmos.000.pp1.nc'], ['expt'])
        results = [Mock(attributes={'omnium_cube_id': i}) for i in range(5)]
        mock_load.return_value = results
        wa.load_results()
        for result in results:
            omnium_cube_id = result.attributes['omnium_cube_id']
            assert wa.results[omnium_cube_id] == result

    @patch('os.path.exists')
    def test_load_results_nonexistant(self, mock_exists):
        mock_exists.return_value = False
        wa = SingleAnalyser(self.suite, 'datam', {'expt': '/path/to/data_dir'}, '',
                            ['atmos.000.pp1.nc'], ['expt'])
        with self.assertRaises(OmniumError):
            wa.load_results()

    @patch.object(SingleAnalyser, 'run_analysis')
    def test_run(self, mock_run_analysis):
        wa = SingleAnalyser(self.suite, 'datam', {'expt': '/path/to/data_dir'}, '',
                            ['atmos.000.pp1.nc'], ['expt'])
        wa.run()
        mock_run_analysis.assert_called_with()

    @patch.object(SingleAnalyser, 'run_analysis')
    @patch('ipdb.runcall')
    def test_run_interactive(self, mock_runcall, mock_run_analysis):
        wa = SingleAnalyser(self.suite, 'datam', {'expt': '/path/to/data_dir'}, '',
                            ['atmos.000.pp1.nc'], ['expt'])
        wa.run(interactive=True)
        mock_runcall.assert_called_with(wa.run_analysis)

    @patch('iris.cube.CubeList')
    @patch('iris.save')
    def test_save(self, mock_save, mock_CubeList):
        wa = SingleAnalyser(self.suite, 'datam', {'expt': '/path/to/data_dir'}, '',
                            ['atmos.000.pp1.nc'], ['expt'])
        wa.save()
        mock_CubeList.assert_called_with([])
        mock_save.assert_not_called()

        results = [('result_{}'.format(i), Mock(attributes={'omnium_cube_id': i}))
                   for i in range(5)]
        for name, result in results:
            wa.results[name] = result
        mock_CubeList.return_value = [r[1] for r in results]
        wa.save()
        mock_CubeList.assert_called_with(wa.results.values())
        mock_save.assert_called()

    def test_display_results(self):
        wa = SingleAnalyser(self.suite, 'datam', {'expt': '/path/to/data_dir'}, '',
                            ['atmos.000.pp1.nc'], ['expt'])

        wa.display()

        wa.display_results = Mock()
        wa.display()
        wa.display_results.assert_called_with()

    @patch('ipdb.runcall')
    def test_display_results_interactive(self, mock_runcall):
        wa = SingleAnalyser(self.suite, 'datam', {'expt': '/path/to/data_dir'}, '',
                            ['atmos.000.pp1.nc'], ['expt'])

        wa.display_results = Mock()
        wa.display(interactive=True)
        mock_runcall.assert_called_with(wa.display_results)

    @patch.object(Analyzer, 'figpath')
    def test_save_text(self, mock_figpath):
        wa = SingleAnalyser(self.suite, 'datam', {'expt': '/path/to/data_dir'}, '',
                            ['atmos.000.pp1.nc'], ['expt'])
        mock_figpath.return_value = 'filename'
        with patch('__builtin__.open', mock_open()) as mock_file:
            wa.save_text('name', 'message')
            mock_file.assert_called_with(*('filename', 'w'))
            handle = mock_file()
            args, kwargs = handle.write.call_args
            assert args[0] == 'message'

    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_figpath(self, mock_makedirs, mock_exists):
        wa = SingleAnalyser(self.suite, 'datam', {'expt': '/path/to/data_dir'}, '',
                            ['atmos.000.pp1.nc'], ['expt'])

        mock_exists.return_value = False
        wa.figpath('steve')
        mock_makedirs.assert_called()
        mock_makedirs.reset_mock()

        mock_exists.return_value = True
        wa.figpath('steve')
        mock_makedirs.assert_not_called()
        mock_makedirs.reset_mock()

        wa.multi_expt = True
        wa.figpath('steve')
