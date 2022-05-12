# -*- coding: utf-8 -*-
# Author: Icy(enderman1024@foxmail.com)
# OS: ALL
# Name: Simple Path Checker
# Description: Make the target path available if it dosen't exist

import os

def path_fixer(path): # path checker
    chk = ""
    ret = False
    for i in path:
        chk += i
        if i in ("/", "\\"):
            if not os.path.exists(chk):
                os.mkdir(chk)
                ret = True
    return ret
