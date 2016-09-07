from glob import glob
import pep8

pep8.MAX_LINE_LENGTH = 100

filenames = sorted(glob('../src/python/omnium/*.py'))
filenames.extend(sorted(glob('../src/python/omnium/omni_cmds/*.py')))
filenames.extend(sorted(glob('../src/python/omnium/omnium_cmds/*.py')))
filenames.extend(sorted(glob('../src/python/omnium/processes/*.py')))
filenames.extend(sorted(glob('pep8_tests/*.py')))
filenames.extend(sorted(glob('cmdline_args/*.py')))


def test_generator():
    for filename in filenames:
        yield _test_conformance_in_file, filename


def _test_conformance_in_file(filename):
    print(filename)
    pep8style = pep8.StyleGuide()
    result = pep8style.check_files([filename])
    assert result.total_errors == 0, "Found code style errors (and warnings)."
