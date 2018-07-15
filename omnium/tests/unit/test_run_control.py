from unittest import TestCase

from mock import Mock, patch

from omnium.run_control.run_control import _find_filenames, _scan_data_dirs
from omnium.setup_logging import setup_logger


# TODO: more tests on runcontrol.


class TestRunControl(TestCase):
    def setUp(self):
        setup_logger()

    @patch('omnium.TaskMaster._get_package_version')
    @patch('glob.glob')
    def test_scan_dirs_empty(self, mock_glob, mock_get_package_version):
        suite = Mock()
        task_master = Mock()
        mock_analysis_cls = Mock()
        mock_analysis_cls.input_dir.format.return_value = '/mock_dir'

        mock_settings = Mock()
        mock_settings.get_hash.return_value = 'abcdefghijklmnop'
        mock_settings.package = Mock()
        mock_get_package_version.return_value = 'pkg_name_v_-99'
        analysis = [('mock_analysis', mock_analysis_cls, True)]

        suite.suite_dir = 'suite_dir'

        mock_glob.return_value = []
        virtual_drive = _scan_data_dirs(['e1', 'e2'], suite, task_master, analysis)
        assert virtual_drive == []

    @patch('omnium.TaskMaster._get_package_version')
    @patch('glob.glob')
    def test_scan_dirs_finds_some(self, mock_glob, mock_get_package_version):
        suite = Mock()
        task_master = Mock()
        mock_analysis_cls = Mock()
        mock_analysis_cls.input_dir.format.return_value = '/mock_dir'

        mock_settings = Mock()
        mock_settings.get_hash.return_value = 'abcdefghijklmnop'
        mock_settings.package = Mock()
        mock_get_package_version.return_value = 'pkg_name_v_-99'
        analysis = [('mock_analysis', mock_analysis_cls, True)]

        suite.suite_dir = 'suite_dir'
        fns = ['fn1', 'fn2']

        def mock_glob_fn(arg):
            print(arg)
            return fns

        mock_glob.side_effect = mock_glob_fn
        virtual_drive = _scan_data_dirs(['e1', 'e2'], suite, task_master, analysis)
        assert mock_glob.call_count == 1
        assert virtual_drive == fns

    @patch('os.path.exists')
    @patch('os.path.abspath')
    def test_find_filenames(self, mock_abspath, mock_exists):
        def mock_exists_fn(fn):
            return True

        mock_exists.side_effect = mock_exists_fn
        mock_abspath.side_effect = lambda x: '/' + x
        fns = ['fn1', 'fn2']
        virtual_drive = _find_filenames(fns)
        output_fns = ['/' + f for f in fns]
        assert(set(virtual_drive) == set(output_fns))
