#!/usr/bin/env python
import os
import sys
try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup, Extension

from omnium.version import get_version


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='omnium',
    version=get_version(),
    description='Output Management with Natural Interface for the UM',
    # long_description=read('README.rst'),
    long_description='',
    author='Mark Muetzelfeldt',
    author_email='m.muetzelfeldt@pgr.reading.ac.uk',
    maintainer='Mark Muetzelfeldt',
    maintainer_email='m.muetzelfeldt@pgr.reading.ac.uk',
    packages=['omnium',
              'omnium.processes', 
              'omnium.omni_cmds',
              'omnium.omnium_cmds'],
    scripts=[
        'bin/omni',
        'bin/omnium',
        ],
    install_requires=[
        ],
    data_files=[('files/vn10.5', ['files/vn10.5/STASHmaster_A']),
                ('templates', ['templates/omni_conf.py.tpl',
                               'templates/computer.txt.tpl',
                               'templates/omni_conf.py.tpl',
                               'templates/omni.info.tpl',
                               'templates/omni_proc.py.tpl'])],
    url='https://github.com/markmuetz/omnium',
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: C',
        'Topic :: Scientific/Engineering :: Atmospheric Science',
        ],
    keywords=[''],
    )
