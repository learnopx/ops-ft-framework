#!/usr/bin/env python

"Setuptools params"

from setuptools import setup, find_packages
from os.path import join

# Get version number from source tree
import sys
sys.path.append('.')

VERSION = "1.0.0"

modname = distname = 'opstestfw'
hostlib = distname + '/host'
switchlib = distname + '/switch'
switchCLIlib = distname + '/switch/CLI'
switchOVSlib = distname + '/switch/OVS'
restEnv = distname + '/restEnv'

setup(
    name=distname,
    version=VERSION,
    description='Feature Level Test Framework for OpenSwitch',
    packages=[
        modname, 
        hostlib, 
        switchlib, 
        switchCLIlib, 
        switchOVSlib,
        restEnv],
    long_description="""
        The opstestfw is the feature and system level test framework
        for OpenSwitch.  This framework provides libraries for automation of
        feature, system, and solution level tests.
        """,
    classifiers=[
          "License :: OSI Approved :: Apache Software License",
          "Programming Language :: Python",
          "Development Status :: 2 - Pre-Alpha",
          "Intended Audience :: Developers",
          "Topic :: Test :: Framework",
    ],
    license='Apache Software License',
    install_requires=[
        'setuptools',
        'mininet',
        'opsvsi'
    ],
    package_data = {'': ['*.crt', '*.key']},
)
