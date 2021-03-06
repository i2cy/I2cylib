# -*- coding: utf-8 -*-
# Author: Icy(enderman1024@foxmail.com)
# OS: ALL
# Name: Shell Argument(s) Decoder
# Description: This function can get the argument(s) from the string

def get_args(opt): # decode command shell's argument(s)
    opts = []
    strin = False
    temp = ""
    for i in opt:
        if strin:
            if not i in ("\"","\'"):
                temp += i
            else:
                strin = False
            continue
        else:
            if i in ("\"","\'"):
                strin = True
                continue
        if i != " ":
            temp += i
        else:
            opts.append(temp)
            temp = ""
    if len(temp) > 0:
        opts.append(temp)
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
