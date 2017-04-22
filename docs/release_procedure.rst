Release Procedure
=================

* Run all tests:

::
    
    cd tests
    source activate omnium_testing
    nosetests
    source deactivate
    cd ..

* Make sure version.py is at correct version:

::

    omnium version

* Commit changes:

::

    git commit -a

* Build docs:

::

    cd docs
    make zip_html

* [Check credentials in `~/.pypirc`]
* Upload to PyPI, run:

::

    python setup.py sdist bdist_wheel
    twine upload dist/*

* Upload docs: go to https://pypi.python.org/pypi?%3Aaction=pkg_edit&name=omnium and upload zip file.

* Tag release with e.g. v0.6.0 and push to github:

::

    git tag v0.6.0
    git push && git push --tags

* Close github milestone (e.g. https://github.com/markmuetz/omnium/milestone/2)
