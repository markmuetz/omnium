import os
from unittest import TestCase

from omnium.analysers import Analysers


class TestAnalysers(TestCase):
    def test_get_analysis_classes_native(self):
        cwd = os.getcwd()
        analysers = Analysers([])
        analysers.find_all()

        assert len(analysers.analysis_classes) == 2

    def test_get_analysis_classes_extra(self):
        cwd = os.getcwd()
        analysers = Analysers([os.path.join(cwd, 'test_analysers')])
        analysers.find_all()

        assert len(analysers.analysis_classes) == 4
