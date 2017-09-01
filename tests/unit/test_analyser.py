from unittest import TestCase
from mock import Mock, patch
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
        patcher = patch('os.makedirs')
        patcher.start()
        self.suite = Mock()
        self.suite.check_filename_missing = lambda x: False

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
