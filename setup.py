#!/usr/bin/env python

from setuptools import setup, find_packages
from pip.req import parse_requirements

install_requirements = parse_requirements('OIPA/requirements.txt', session=False)
requirements = [str(ir.req) for ir in install_requirements]

setup(name='OIPA',
      version='2.2.2',
      author='Zimmerman & Zimmerman',
      description="OIPA is an open-source framework that renders IATI compliant XML and \
            related indicator #opendata into the OIPA datamodel for storage. \
            This ETL approach provides I/O using the OIPA Tastypie RESTless API (soon DRF!) \
            providing you with direct XML or JSON output. Does Django and MySQL. \
            Codebase maintained by Zimmerman & Zimmerman in Amsterdam. http://www.oipa.nl/",
      url='https://github.com/catalpainternational/oipa',
      packages=find_packages('OIPA'),  # iati, etc
      package_dir={'': 'OIPA'},
      install_requires=requirements,
      zip_safe=False
      )
