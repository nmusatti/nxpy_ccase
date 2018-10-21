# nxpy_ccase ------------------------------------------------------------------

# Copyright Nicola Musatti 2018
# Use, modification, and distribution are subject to the Boost Software
# License, Version 1.0. (See accompanying file LICENSE.txt or copy at
# http://www.boost.org/LICENSE_1_0.txt)

# See https://github.com/nmusatti/nxpy_ccase. ---------------------------------

r"""
Packaging information.

"""

from __future__ import absolute_import

import codecs
import os

from setuptools import setup

lib_name = 'nxpy_ccase'

here = os.path.abspath(os.path.dirname(__file__))
with codecs.open(os.path.join(here,'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name=lib_name,
    version="1.0.0",
    author="Nicola Musatti",
    author_email="nicola.musatti@gmail.com",
    description = "A wrapper for Clear Case's cleartool utility",
    long_description = long_description,
    project_urls={
        "Documentation": "https://nxpy_ccase.readthedocs.io/en/latest/",
        "Source Code": "https://github.com/nmusatti/nxpy_ccase",
    },
    license="Boost Software License 1.0 (BSL-1.0)",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Boost Software License 1.0 (BSL-1.0)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries',
    ],
    namespace_packages=['nxpy'],
    packages=['nxpy.ccase'],
    install_requires=[
        'six',
        'nxpy_command',
        'nxpy_path',
        'nxpy_test',
    ],
)
