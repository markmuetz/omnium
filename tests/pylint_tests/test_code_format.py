import os
from pylint.lint import Run


def _get_python_filenames(dirname):
    filenames = []
    for root, dirs, files in os.walk(dirname):
        for f in files:
            if f.endswith(".py"):
                filenames.append(os.path.join(root, f))
    return filenames


def test_pylint_src():
    filenames = _get_python_filenames('../src/python')
    pylint_run = _test_pylint(filenames)
    yield _test_score, pylint_run, 6
    yield _test_errors, pylint_run, 0


def test_pylint_tests():
    filenames = _get_python_filenames('.')
    pylint_run = _test_pylint(filenames)
    yield _test_score, pylint_run, 5
    yield _test_errors, pylint_run, 1


def _test_pylint(filenames):
    pylint_run = Run(['--rcfile=pylint_tests/pylint.rc'] + filenames, exit=False)
    return pylint_run


def _test_score(pylint_run, min_score):
    error = pylint_run.linter.stats['error']
    warning = pylint_run.linter.stats['warning']
    refactor = pylint_run.linter.stats['refactor']
    convention = pylint_run.linter.stats['convention']
    statement = pylint_run.linter.stats['statement']
    score = 10.0 - ((float(5 * error + warning +
                           refactor + convention) / statement) * 10)
    assert score > min_score, "PyLint score of {0:.1f} too high".format(score)


def _test_errors(pylint_run, max_error):
    error = pylint_run.linter.stats['error']
    assert error <= max_error, "PyLint detected too many errors: {0} too high".format(error)
