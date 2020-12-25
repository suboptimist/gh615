# SQ100 - Serial Communication with the a-rival SQ100 heart rate computer
# Copyright (C) 2017  Timo Nachstedt
#
# This file is part of SQ100.
#
# SQ100 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SQ100 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function
from setuptools import setup


setup(
    name='sq100',
    version="0.1.1",
    url='http://github.com/tnachstedt/sq100/',
    license='Apache Software License',
    author='Timo Nachstedt',
    tests_require=['pytest', 'pytest-pep8', 'mock'],
    setup_requires=['pytest-runner>=2.9,<3dev'],
    install_requires=['pyserial>=3.0,<4.0',
                      'tabulate>=0.7,<1.0'],
    author_email='mail@nachstedt.com',
    description='Alternative read out for the SQ 100 heart rate monitor',
    long_description="""
      Alternative read out for the SQ 100 heart rate monitor
    """,
    packages=['sq100'],
    include_package_data=True,
    platforms='any',
    test_suite='sq100.test.test_sq100',
    entry_points={
        "console_scripts": ["sq100 = sq100.sq100:main"]},
    classifiers=[
        'Programming Language :: Python',
        'Development Status :: 1 - Planning',
        'Natural Language :: English',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Topic :: Utilities',
    ],
    extras_require={
        'dev': [
            'autopep8',
            "mock",
            'mypy==0.782',  # to avoid python/mypy#9656
            'pip-tools',
            'pytest',
            'pytest-flake8',
            'pytest-cov'
        ]
    }
)
