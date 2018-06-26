from unittest import TestCase

from mock import Mock, patch, mock_open

from omnium.analyser_setting import AnalyserSetting
import omnium


class TestAnalyserSetting(TestCase):
    def test_init_empty(self):
        setting = AnalyserSetting(omnium)

    def test_init_with_dict(self):
        setting = AnalyserSetting(omnium, {'a': 1, 'b': 'sheep'})

    def test_init_with_slice(self):
        setting = AnalyserSetting(omnium, {'sl': slice(1, 20, 3), 'b': 'sheep'})

    def test_init_with_bad_key(self):
        with self.assertRaises(AssertionError):
            setting = AnalyserSetting(omnium, {1: 'a', 'b': 'sheep'})

    def test_get_attr(self):
        setting = AnalyserSetting(omnium, {'sl': slice(1, 20, 3), 'b': 'sheep'})
        assert setting.sl == slice(1, 20, 3)
        setting.b == 'sheep'

    @patch('omnium.AnalyserSetting.from_json')
    def test_load(self, mock_from_json):
        setting = AnalyserSetting(omnium)
        with patch('builtins.open', mock_open()) as mock_file:
            setting.load('loc')
            mock_file.assert_called_with(*('loc', 'r'))

    def test_save(self):
        setting = AnalyserSetting(omnium, {'a': 1, 'b': 'sheep'})
        with patch('builtins.open', mock_open()) as mock_file:
            setting.save('loc')
            mock_file.assert_called_with(*('loc', 'w'))
            handle = mock_file()
            args, kwargs = handle.write.call_args
            assert args[0] == setting.to_json()

    def test_to_from_json(self):
        setting = AnalyserSetting(omnium, {'a': 1, 'b': 'sheep'})
        setting2 = AnalyserSetting(omnium)
        setting_json = setting.to_json()
        setting2.from_json(setting_json)
        assert setting == setting2

    def test_to_from_json_with_slice(self):
        setting = AnalyserSetting(omnium, {'sl': slice(1, 20, 3), 'b': 'sheep'})
        setting2 = AnalyserSetting(omnium)
        setting_json = setting.to_json()
        setting2.from_json(setting_json)
        assert setting == setting2

    def test_get_hash(self):
        setting = AnalyserSetting(omnium, {'sl': slice(1, 20, 3), 'b': 'sheep'})
        assert setting.get_hash()

    def test_eq1(self):
        setting1 = AnalyserSetting(omnium, {'sl': slice(1, 20, 3), 'b': 'sheep'})
        setting2 = AnalyserSetting(omnium, {'sl': slice(1, 20, 3), 'b': 'sheep'})
        assert setting1 == setting2

    def test_eq2(self):
        setting1 = AnalyserSetting(omnium, {'b': 'sheep', 'sl': slice(1, 20, 3)})
        setting2 = AnalyserSetting(omnium, {'sl': slice(1, 20, 3), 'b': 'sheep'})
        assert setting1 == setting2

    def test_ne1(self):
        import sys
        setting1 = AnalyserSetting(sys, {'sl': slice(1, 20, 3), 'b': 'sheep'})
        setting2 = AnalyserSetting(omnium, {'sl': slice(1, 20, 3), 'b': 'sheep'})
        assert setting1 != setting2

    def test_ne2(self):
        setting1 = AnalyserSetting(omnium, {'sl': slice(1, 20, 3), 'b': 3})
        setting2 = AnalyserSetting(omnium, {'sl': slice(1, 20, 3), 'b': 'sheep'})
        assert setting1 != setting2

    def test_ne3(self):
        setting1 = AnalyserSetting(omnium, {'sl': slice(1, 20, 4), 'b': 3})
        setting2 = AnalyserSetting(omnium, {'sl': slice(1, 20, 3), 'b': 3})
        assert setting1 != setting2
