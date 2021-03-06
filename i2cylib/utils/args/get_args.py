# -*- coding: utf-8 -*-
# Author: Icy(enderman1024@foxmail.com)
# OS: ALL
# Name: Shell Argument(s) Reader
# Description: This function can get the argument(s) from the Shell
# Used Librarie(s): sys

import sys

def get_args(): # read command shell's argument(s)
    opts = sys.argv[1:]
    argv = ""
    res = {}
    for i in opts:
        if len(argv) > 0 and "-" != i[0]:
            res.update({argv:i})
            argv = ""
        if "-" == i[0]:
            argv = i
            res.update({argv:""})
    return res
