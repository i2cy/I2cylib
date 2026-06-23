#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Filename: __init__.py
# Created on: 2021/3/6

import warnings

try:
    from ._icfat64 import IcFAT, icfat_test
except ImportError as e:
    warnings.warn(
        "i2cylib.filesystem: C++ extension unavailable ({}), "
        "falling back to pure Python implementation. "
        "Performance will be degraded.".format(e)
    )
    from .icfat import IcFAT, icfat_test
