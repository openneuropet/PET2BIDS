#!/usr/bin/env python

"""The setup script."""
import os

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

if os.path.exists('requirements.txt'):
    with open('requirements.txt') as requirements_file:
        requirements = requirements_file.readlines()
        requirements = [requirement.strip('\n') for requirement in requirements]
else:
    requirements = []

test_requirements = []

setup(
    author="anthony galassi",
    author_email='28850131+bendhouseart@users.noreply.github.com',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    description="A python utility for converting ecat images into nifti's and jsons and BIDS oh my!",
    entry_points={
        'console_scripts': [
            'pet2bids=pet2bids.cli:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='pet2bids',
    name='pet2bids',
    packages=find_packages(include=['pet2bids', 'pet2bids.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/bendhouseart/pet2bids',
    version='0.0.0',
    zip_safe=False,
)
