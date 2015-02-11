# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "valinor",
    version = "0.0.0",
    author = "James Crosby",
    author_email = "James.Crosby@arm.com",
    description = ("Re-usable components for embedded software."),
    license = "Apache-2.0",
    keywords = "embedded package module dependency management",
    url = "about:blank",
    packages=find_packages(),
    package_data={
        'valinor': ['templates/*.tmpl']
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
    test_suite = 'valinor.test',
    install_requires=[
        'pyyaml>=3,<4',
        'Jinja2>=2.7.0,<3',
        'setuptools>=12',
    ]
)
