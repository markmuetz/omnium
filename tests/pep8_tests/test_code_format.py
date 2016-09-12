import os
import pep8

pep8.MAX_LINE_LENGTH = 100


def _get_python_filenames(dirname):
    filenames = []
    for root, dirs, files in os.walk(dirname):
        for f in files:
            if f.endswith(".py"):
                filenames.append(os.path.join(root, f))
    return filenames


def test_src_generator():
    filenames = _get_python_filenames('../src/python')
    for filename in filenames:
        yield _test_conformance_in_file, filename


def test_tests_generator():
    filenames = _get_python_filenames('.')
    for filename in filenames:
        yield _test_conformance_in_file, filename


def _test_conformance_in_file(filename):
    print(filename)
    pep8style = pep8.StyleGuide()
    result = pep8style.check_files([filename])
    assert result.total_errors == 0, "Found code style errors (and warnings)."
