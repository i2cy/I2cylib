# -*- coding: utf-8 -*-
# Author: Icy(enderman1024@foxmail.com)
# OS: ALL
# Name: Path String Reader
# Description: Read a string-type path and return (path,filename)


def read_path(path): # Path String Reader
    pathx = ""
    temp = ""
    for i in path:
        temp += i
        if i in ("/", "\\"):
            pathx += temp
            temp = ""
    name = temp
    return pathx, name
