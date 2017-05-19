#!/usr/bin/env python
import os
import sys
try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup, Extension

from omnium.version import get_version


def read(fname):
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except:
        return ''


setup(
    name='omnium',
    version=get_version(),
    description='Output Management with Natural Interface for the UM',
    long_description=read('readme.rst'),
    author='Mark Muetzelfeldt',
    author_email='m.muetzelfeldt@pgr.reading.ac.uk',
    maintainer='Mark Muetzelfeldt',
    maintainer_email='m.muetzelfeldt@pgr.reading.ac.uk',
    packages=['omnium',
              'omnium.cmds',
              'omnium.data', 
              'omnium.viewers', 
              'omnium.viewers.data_displays'],
    scripts=[
        'bin/omnium',
        ],
    install_requires=[
        ],
    package_data={'omnium.data': ['files/vn10.5/STASHmaster*'],
        },
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
