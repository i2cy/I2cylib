#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Filename: normal_delay
# Created on: 2021/4/18


import time
import numpy as np


class NormalIncreasingDelay:

    def __init__(self, delay_counts, total_delay_s, warning=True, auto_fix=True):
        self.delay_list = []
        self.num = delay_counts
        self.total_delay = total_delay_s
        self.offset = 0

        self.fix = 0

        self.warning = warning
        self.warning_level = 0
        self.auto_fix = auto_fix

        self.last_delayed = -1

        self.generate()

    def seek(self, offset=0):
        self.last_delayed = -1
        if offset < 0:
            offset = len(self.delay_list) + offset
        self.offset = offset

    def delay(self):
        delay_time = self.delay_list[self.offset]
        if self.last_delayed > 0:
            need = delay_time - (time.time() - self.last_delayed) + self.fix
            if need < 0:
                if need < self.fix:
                    self.warning_level += 1
                if self.warning_level > 10 and self.warning:
                    print("warning: can not keep up, total delay time may be longer"
                          ". you should make your program run faster")
                self.fix = need
                need = 0
            else:
                if self.warning_level >= 1:
                    self.warning_level -= 1
        else:
            need = delay_time
        time.sleep(need)
        self.offset += 1
        self.last_delayed = time.time()

    def generate(self):
        dots = np.random.randn(self.num)
        for i, ele in enumerate(dots):
            if ele < 0:
                dots[i] = -ele
        dots *= (self.total_delay/dots.max())
        dots.sort()
        last = 0
        res = []
        for ele in dots:
            res.append(ele-last)
            last = ele
        self.delay_list = res

        return res