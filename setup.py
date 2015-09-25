#!/usr/bin/env python

from setuptools import setup, find_packages

requirements = [
    'celery',
    'pretty_cron',
    'sqlalchemy',
]


readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')


setup(
    name='celerycontrib.sqlalchemyscheduler',
    version='0.1.1-dev0',
    packages=find_packages(),
    namespace_packages=['celerycontrib'],
    include_package_data=True,
    install_requires=requirements,

    description='SQLAlchemy-backed scheduler for Celery',
    long_description=readme + '\n\n' + history,
    author='Arthur Blair',
    author_email='adblair@gmail.com',
    keywords='celerycontrib.sqlalchemyscheduler',
    classifiers=[
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
    ],
)
