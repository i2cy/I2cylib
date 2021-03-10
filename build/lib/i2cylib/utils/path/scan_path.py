# -*- coding: utf-8 -*-
# Author: Icy(enderman1024@foxmail.com)
# OS: ALL
# Name: File Path Scanner
# Description: Scan the file and folders in target path with top mode and all mode
# Used Librarie(s): os

import os

def scan_path(patho, mode): # list file(s) & folder(s)
    paths = []
    files = []
    pathx = ""
    for i in patho:
        if i in ("\\","/"):
            pathx += os.sep
        else:
            pathx += i
    if os.sep != pathx[-1:]:
        target_path = pathx + os.sep
    else:
        target_path = pathx
    if mode == "top":
        res = os.listdir(target_path)
        for i in res:
            if os.path.isfile(target_path + i):
                files.append(target_path + i)
            else:
                paths.append(target_path + i)
    elif mode == "all":
        res = os.walk(target_path)
        for path,d,filelist in res:
            if path[-1] != os.sep:
                paths.append(path + os.sep)
            else:
                paths.append(path)
            for filename in filelist:
                files.append(os.path.join(path,filename))
    return paths, files
