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

* Check all omnis (on all computers using sync'd git omnium):

::

    cd ~/omnis/
    omnium-check-omnis.sh <comp> > checks_v0.6.0.out
    cd -

* [Check credentials in `~/.pypirc`]
* Upload to PyPI, run:

::

    python setup.py sdist upload

* Tag release with e.g. v0.6.0 and push to github:

::

    git tag v0.6.0
    git push && git push --tags

* Upload docs, run:

::

    cd docs
    make zip_html
    cd ..

* Then go to https://pypi.python.org/pypi?%3Aaction=pkg_edit&name=omnium and upload zip file.

* Close github milestone (e.g. https://github.com/markmuetz/omnium/milestone/2)
