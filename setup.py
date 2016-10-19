#!/usr/bin/env python

from distutils.core import setup
from setuptools import find_packages
from pip.req import parse_requirements

install_requirements = parse_requirements('OIPA/requirements.txt', session=False)
requirements = [str(ir.req) for ir in install_requirements]

setup(name='OIPA',
      version='2.5.2',
      author='Catalpa',
      description='A fork of https://github.com/zimmerman-zimmerman/OIPA used at Catalpa.',
      url='https://github.com/catalpainternational/oipa',
      packages=find_packages('OIPA'),  # iati, etc
      package_dir={'': 'OIPA'},
      install_requires=requirements,
      zip_safe=False
      )
