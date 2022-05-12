#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Filename: echo
# Created on: 2021/4/18

import sys
import time


class Echo:

    def __init__(self, tab_size=8):

        self.tab_size = tab_size
        self.buttom_line = ""
        self.busy = False

    def __wait(self):
        while self.busy:
            time.sleep(0.01)

    def print(self, msg):
        msg = str(msg)

        fill_length = len(self.buttom_line)
        for i in self.buttom_line:
            if i == "\t":
                fill_length += self.tab_size - 1

        self.__wait()
        self.busy = True

        try:
            sys.stdout.write("\r" + fill_length * " " + "\r")
            sys.stdout.flush()
            sys.stdout.write(msg + "\n")
            sys.stdout.write(self.buttom_line)
            sys.stdout.flush()
        except:
            pass

        self.busy = False

    def buttom_print(self, msg):
        msg = str(msg)

        fill_length = len(self.buttom_line)
        for i in self.buttom_line:
            if i == "\t":
                fill_length += self.tab_size - 1

        self.__wait()
        self.busy = True

        try:
            sys.stdout.write("\r" + fill_length * " " + "\r")
            sys.stdout.flush()
            sys.stdout.write(msg)
            self.buttom_line = msg
            sys.stdout.flush()
        except:
            pass

        self.busy = False


if __name__ == '__main__':
    ECHO = Echo()
    ECHO.buttom_print("This Is Buttom Message")
    for i in range(10):
        time.sleep(1)
        ECHO.print("this is normal message {}".format(i))