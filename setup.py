#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The setup script."""

import sys

from setuptools import find_packages, setup

author = "Dave Vandenbout"
email = "devb@xess.com"
version = "1.0.0"

if "sdist" in sys.argv[1:]:
    with open("kinjector/pckg_info.py", "w") as f:
        for name in ["author", "email", "version"]:
            f.write("{} = '{}'\n".format(name, locals()[name]))

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = [
    "pyyaml",
]

setup_requirements = [
    "pytest-runner",
]

test_requirements = [
    "pytest",
]

setup(
    author=author,
    author_email=email,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Manufacturing",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
    ],
    description="Inject/eject JSON/YAML data to/from KiCad files.",
    entry_points={"console_scripts": ["kinjector=kinjector.cli:main",],},
    install_requires=requirements,
    license="MIT license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="kinjector",
    name="kinjector",
    packages=find_packages(include=["kinjector"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/devbisme/kinjector",
    project_urls={
        "Documentation": "https://devbisme.github.io/kinjector",
        "Source": "https://github.com/devbisme/kinjector",
        "Changelog": "https://github.com/devbisme/kinjector/blob/master/HISTORY.rst",
        "Tracker": "https://github.com/devbisme/kinjector/issues",
    },
    version=version,
    zip_safe=False,
)
