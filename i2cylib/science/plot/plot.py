#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: I2cylib
# Filename: plot
# Created on: 2022/7/4

import matplotlib
import matplotlib.pyplot as plt


class EasyPlot2D(object):

    def __init__(self, data):
        """
        EasyPlot2D, convert any formatted string to List like object to plot.

        :param data: str, List, ndarray
        """
        if isinstance(data, str):
            if "\t" in data:
                pass
