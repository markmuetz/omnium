Running tests
=============

Enable python3 and activate any envs as necessary. From the tests dir, run:

::

    # All:
    nosetests
    # Individual:
    nosetests pep8_tests

ARCHER
------

How to run on ARCHER::

    qserial
    # Aliased to "qsub -IVl select=serial=true:ncpus=1,walltime=10:0:0 -A n02-REVCON"
    source ~/.anaconda3_setup.sh
    source activate /home/n02/n02/mmuetz/work/conda/envs/iris36
    cd work/omnium/tests
    nosetests

N.B. any tests involving pyqtgraph (with windows) will not work due to glibc incompatibility.
