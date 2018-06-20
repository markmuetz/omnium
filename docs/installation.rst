.. _installation_pip:

Installation using pip
======================

::

    pip install omnium

Development installation using pip
==================================

::

    git clone https://github.com/markmuetz/omnium
    cd omnium
    # Install optional viewer package.
    pip install -e .[viewer]

Deploying on HPC installation
=============================

::

    git clone https://github.com/markmuetz/omnium
    cd omnium
    # Install optional shell and viewer packages.
    pip install -e .[HPC]
