import os
from unittest import TestCase
from mock import Mock, patch, mock_open

from omnium.analyzers import get_analysis_classes
from omnium.analyzer import Analyzer
from omnium import OmniumError


class TestAnalyzers(TestCase):
    def test_get_analysis_classes(self):
        cwd = os.getcwd()
        analysis_classes = get_analysis_classes(os.path.join(cwd, 'test_analysers'))
        assert len(analysis_classes) == 1
