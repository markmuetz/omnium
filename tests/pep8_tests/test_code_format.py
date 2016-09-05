from glob import glob
import pep8


class TestCodeFormat:
    def __init__(self):
        # set max line length to something more accommodating.
        pep8.MAX_LINE_LENGTH = 100
        self.pep8style = pep8.StyleGuide()

    def _test_conformance_in_files(self, filenames):
        assert len(filenames) != 0
        for filename in sorted(filenames):
            result = self.pep8style.check_files([filename])
            assert result.total_errors == 0, "Found code style errors (and warnings)."

    def test_1_omnium_pep8_conformance(self):
        """Test that omnium module conforms to PEP8. (Bar E501)"""
        filenames = glob('../src/python/omnium/*.py')
        self._test_conformance_in_files(filenames)

    def test_2_omni_cmds_pep8_conformance(self):
        """Test that omni_cmds module conforms to PEP8. (Bar E501)"""
        filenames = glob('../src/python/omnium/omni_cmds/*.py')
        self._test_conformance_in_files(filenames)

    def test_3_omnium_cmds_pep8_conformance(self):
        """Test that omnium_cmds module conforms to PEP8. (Bar E501)"""
        filenames = glob('../src/python/omnium/omnium_cmds/*.py')
        self._test_conformance_in_files(filenames)

    def test_4_processes_pep8_conformance(self):
        """Test that processes module conforms to PEP8. (Bar E501)"""
        filenames = glob('../src/python/omnium/processes/*.py')
        self._test_conformance_in_files(filenames)

    def test_6_tests_pep8_conformance(self):
        """Test that all tests conforms to PEP8. (Bar E501)"""
        filenames = glob('pep8_tests/*.py')
        self._test_conformance_in_files(filenames)
