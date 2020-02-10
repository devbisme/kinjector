#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The setup script."""

import sys

from setuptools import find_packages, setup

author = "XESS Corp."
email = "info@xess.com"
version = "0.0.6"

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
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
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
    url="https://github.com/xesscorp/kinjector",
    version=version,
    zip_safe=False,
)
