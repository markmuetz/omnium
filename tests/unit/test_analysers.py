import os
from unittest import TestCase
from mock import Mock, patch, mock_open

from omnium.analysers import get_analysis_classes
from omnium.analyser import Analyser
from omnium import OmniumError


class TestAnalysers(TestCase):
    def test_get_analysis_classes(self):
        cwd = os.getcwd()
        analysis_classes = get_analysis_classes(os.path.join(cwd, 'test_analysers'))
        assert len(analysis_classes) == 1
