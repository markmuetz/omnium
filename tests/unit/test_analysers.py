import os
from unittest import TestCase

from omnium.analysers import get_analysis_classes


class TestAnalysers(TestCase):
    def test_get_analysis_classes(self):
        cwd = os.getcwd()
        analysis_classes = get_analysis_classes(os.path.join(cwd, 'test_analysers'))
        assert len(analysis_classes) == 2
