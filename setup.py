#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Filename: setup
# Created on: 2021/3/6

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="i2cylib", # Replace with your own username
    version="1.1.0",
    author="I2cy Cloud",
    author_email="i2cy@outlook.com",
    description="A Python library contains a lot of useful functions and tools",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/i2cy/i2cylib",
    project_urls={
        "Bug Tracker": "https://github.com/i2cy/i2cylib/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
)