# -*- coding: utf-8 -*-
# Author: Icy(enderman1024@foxmail.com)
# OS: Windows
# Name: Windows Tasklist
# Used Librarie(s): os
# Version: 1.2

import os

def win_tasklist():# windows tasklist (return data format: [Img_Name, PID, Used_RAM])
    pipe = os.popen("tasklist /fo csv")
    data = pipe.read()
    pipe.close()
    res = (data.split("\n"))[1:-1]
    n = 0
    for i in res:
        data = i.replace("\"","").split(",")
        data = data[:2] + [data[-1]]
        res[n] = data
        n += 1
    return res
