.. _installation_pip:

Installing omnium and dependencies
==================================

::

    # Assumes you have python3 from anaconda installed.
    # Only tested on linux.
    # see: https://www.anaconda.com/download/#linux
    git clone https://github.com/markmuetz/omnium
    cd omnium
    # Install conda requirements
    conda create -n omnium_env --file installation/conda_reqs.txt
    # Active conda env.
    source activate omnium_env
    # Install pip requirements
    pip install -r installation/pip_reqs.txt
    # Install omnium
    pip install -e .

Testing installation
====================

::

    source activate omnium_env
    # Should show current onmium version
    omnium version
    # Requires ssh access into localhost
    # Some tools are required to test: ssh and rsync.
    omnium test
