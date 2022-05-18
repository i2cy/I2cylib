# -*- coding: utf-8 -*-
# Author: Icy(enderman1024@foxmail.com)
# OS: ALL
# Name: Shell Argument(s) Reader
# Description: This function can get the argument(s) from the Shell
# Used Libraries : sys


import sys


def get_args():  # read command shell's argument(s)
    """
    read command shell's argument(s)

    :return: dict
    """
    opts = sys.argv[1:]
    argv = ""
    res = {}
    unlabeled = 0
    for i in opts:
        if len(argv) > 0 and "-" != i[0]:  # 获取标签
            res.update({argv: i})
            argv = ""
        elif "-" == i[0]:
            argv = i
            res.update({argv: ""})
        else:
            res.update({unlabeled: i})
            unlabeled += 1
    return res
