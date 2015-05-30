#!/usr/bin/env python

from setuptools import setup

setup(name='metriccounter',
      version='0.0.3',
      description='Metric Counter for recording time series',
      author='Slawek Ligus',
      author_email='root@ooz.ie',
      url='https://github.com/oozie/metriccounter',
      py_modules=['metriccounter'],
      test_suite="tests",
      classifiers=[
          'License :: OSI Approved :: MIT License',
          'Topic :: System :: Monitoring',
          'Operating System :: POSIX',
          'Operating System :: POSIX :: Linux',
          'Intended Audience :: Developers',
      ],
)
