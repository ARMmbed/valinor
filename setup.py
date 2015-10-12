# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

import os
from setuptools import setup, find_packages

def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()
    return None

setup(
    name = "valinor",
    version = "0.0.10",
    author = 'Martin Kojtal, Matthew Else, James Crosby',
    author_email = "c0170@rocketmail.com, matthewelse1997@gmail.com, James.Crosby@arm.com",
    description = ("Generate IDE project files to debug ELF files."),
    license = "Apache-2.0",
    keywords = "debug c cpp project generator embedded",
    url = "about:blank",
    packages=find_packages(),
    package_data={
    },
    long_description=read('docs/pypi.txt'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: Apache Software License",
        "Environment :: Console",
    ],
    entry_points={
        "console_scripts": [
            "valinor=valinor:main",
        ],
    },
    test_suite = 'nose.collector',
    install_requires=[
        'pyyaml>=3,<4',
        'Jinja2>=2.7.0,<3',
        'setuptools',
        'colorama>=0.3,<0.4',
        'pyOCD>=0.3,<1.0',
        'project_generator>=0.7.0,<0.8.0'
    ],
    tests_require=[
        'nose',
    ]
)
