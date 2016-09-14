Initial setup
=============

Create the testing env with all requirements and a link to the live dir (`pip install -e`) (start in
..):

::

    conda create --name omnium_testing --file conda_reqs.txt
    source activate omnium_testing
    conda install -c scitools --file conda_scitools_reqs.txt
    pip install -e .

Running tests
=============

Before testing, activate the `omnium_testing` env:

::

    source activate omnium_testing

From the tests dir, run:

::

    # All:
    nosetests
    # Individual:
    nosetests cmdline_args
    nosetests pep8_tests
    nosetests pylint_tests
    nosetests unit

Because of the way `omnium` was added to the `omnium_testing` env , all code changes will be picked
up by tests.
