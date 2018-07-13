import os
import sys
from unittest import TestCase

from omnium.analysis import AnalysisPkgs


class TestAnalysers(TestCase):
    def test_get_analyser_classes_extra(self):
        cwd = os.getcwd()
        # If nosetests launched in unit dir, find higher 'test' dir.
        if os.path.basename(cwd) != 'tests':
            cwd = os.path.join(*os.path.split(cwd)[:-1])
        print(cwd)
        sys.path.insert(0, os.path.join(cwd, 'test_analysers'))
        analysis_pkgs = AnalysisPkgs(['analysis'])

        assert len(analysis_pkgs.analyser_classes) == 2
