from unittest import TestCase

from mock import patch, mock_open

from omnium.analysis import AnalysisSettings


class TestAnalyserSetting(TestCase):
    def test_init_empty(self):
        setting = AnalysisSettings()

    def test_init_with_dict(self):
        setting = AnalysisSettings({'a': 1, 'b': 'sheep'})

    def test_init_with_slice(self):
        setting = AnalysisSettings({'sl': slice(1, 20, 3), 'b': 'sheep'})

    def test_init_with_bad_key(self):
        with self.assertRaises(AssertionError):
            setting = AnalysisSettings({1: 'a', 'b': 'sheep'})

    def test_get_attr(self):
        setting = AnalysisSettings({'sl': slice(1, 20, 3), 'b': 'sheep'})
        assert setting.sl == slice(1, 20, 3)
        setting.b == 'sheep'

    @patch('omnium.AnalysisSettings.from_json')
    def test_load(self, mock_from_json):
        setting = AnalysisSettings()
        with patch('builtins.open', mock_open()) as mock_file:
            setting.load('loc')
            mock_file.assert_called_with(*('loc', 'r'))

    def test_save(self):
        setting = AnalysisSettings({'a': 1, 'b': 'sheep'})
        with patch('builtins.open', mock_open()) as mock_file:
            setting.save('loc')
            mock_file.assert_called_with(*('loc', 'w'))
            handle = mock_file()
            args, kwargs = handle.write.call_args
            assert args[0] == setting.to_json()

    def test_to_from_json(self):
        setting = AnalysisSettings({'a': 1, 'b': 'sheep'})
        setting2 = AnalysisSettings()
        setting_json = setting.to_json()
        setting2.from_json(setting_json)
        assert setting == setting2

    def test_to_from_json_with_slice(self):
        setting = AnalysisSettings({'sl': slice(1, 20, 3), 'b': 'sheep'})
        setting2 = AnalysisSettings()
        setting_json = setting.to_json()
        setting2.from_json(setting_json)
        assert setting == setting2

    def test_get_hash(self):
        setting = AnalysisSettings({'sl': slice(1, 20, 3), 'b': 'sheep'})
        assert setting.get_hash()

    def test_eq1(self):
        setting1 = AnalysisSettings({'sl': slice(1, 20, 3), 'b': 'sheep'})
        setting2 = AnalysisSettings({'sl': slice(1, 20, 3), 'b': 'sheep'})
        assert setting1 == setting2

    def test_eq2(self):
        setting1 = AnalysisSettings({'b': 'sheep', 'sl': slice(1, 20, 3)})
        setting2 = AnalysisSettings({'sl': slice(1, 20, 3), 'b': 'sheep'})
        assert setting1 == setting2

    def test_ne2(self):
        setting1 = AnalysisSettings({'sl': slice(1, 20, 3), 'b': 3})
        setting2 = AnalysisSettings({'sl': slice(1, 20, 3), 'b': 'sheep'})
        assert setting1 != setting2

    def test_ne3(self):
        setting1 = AnalysisSettings({'sl': slice(1, 20, 4), 'b': 3})
        setting2 = AnalysisSettings({'sl': slice(1, 20, 3), 'b': 3})
        assert setting1 != setting2
