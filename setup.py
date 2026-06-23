#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Filename: setup
# Created on: 2021/3/6

import setuptools
import re

# Read version without triggering full i2cylib import chain
with open("i2cylib/__init__.py", "r", encoding="utf-8") as f:
    _content = f.read()
__VERSION__ = re.search(r"__VERSION__\s*=\s*['\"]([^'\"]+)['\"]", _content).group(1)

try:
    from pybind11.setup_helpers import Pybind11Extension, build_ext
    HAS_PYBIND11 = True
except ImportError:
    HAS_PYBIND11 = False


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

ext_modules = []
cmdclass = {}

if HAS_PYBIND11:
    ext_modules = [
        Pybind11Extension(
            "i2cylib.filesystem.icfat64._icfat64",
            ["i2cylib/filesystem/icfat64/icfat64.cpp"],
            cxx_std=17,
        ),
    ]
    cmdclass = {"build_ext": build_ext}

setuptools.setup(
    name="i2cylib",
    version=__VERSION__,
    author="I2cy Cloud",
    author_email="i2cy@outlook.com",
    description="A Python library contains a lot of useful functions and tools",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/i2cy/i2cylib",
    project_urls={
        "Bug Tracker": "https://github.com/i2cy/i2cylib/issues",
        "Source Code": "https://github.com/i2cy/i2cylib",
        "Documentation": "https://github.com/i2cy/I2cylib/wiki/API-Document"
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'numpy',
        'tqdm',
        'rsa',
        'pyserial',
        'matplotlib',
        'hidapi'
    ],
    packages=setuptools.find_packages(),
    ext_modules=ext_modules,
    cmdclass=cmdclass,
    python_requires=">=3.6",
    entry_points={'console_scripts':
        [
            "i2cydbserver = i2cylib.database.I2DB.i2cydbserver:main",
            "i2en = i2cylib.crypto.I2En.icen:main",
            "i2scan = i2cylib.network.I2Scan.i2scan:main"
        ]
    }
)
