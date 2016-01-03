#!/usr/bin/python

from setuptools import setup, find_packages

setup(
    name='onemirror',
    version='0.0.1',
    description='OneDrive mirroring program: create a complete mirror of OneDrive contents',
    url='https://github.com/DMOJ/onemirror',
    author='Quantum',
    author_email='quantum@dmoj.ca',
    license='GPLv3',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='onedrive mirror file network sync',
    packages=find_packages(),
    install_requires=['python-dateutil', 'requests'],

    entry_points={
        'console_scripts': [
            'onemirror=onemirror.main:main',
        ],
    },
)