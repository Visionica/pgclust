#!/usr/bin/env python

from distutils.core import setup

setup(name='pgclust',
    version='1.0',
    description='Stupid postgres cluster manager',
    author='Andrey Tolstoy',
    author_email='avtolstoy@gmail.com',
    url='http://tolstoy.it',
    packages=['pgclust'],
    data_files=[('/usr/sbin', ['pgclust'])]
    )