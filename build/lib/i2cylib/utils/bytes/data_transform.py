# -*- coding: utf-8 -*-
# Author: Icy(enderman1024@foxmail.com)
# OS: ALL
# Name: Bytes data transform
# Description: This function can transform bytes into readable strings


def data_transform(data,format="hex+string"): #data_format: hex+string, hex, string
    strings = [9,10,13] + list(range(32,127))
    res = ""
    if format == "hex+string":
        tag = False
        for i in data:
            if i in strings:
                if tag:
                    res += "]+"
                    tag = False
                if i == 9:
                    res += "\\t"
                elif i == 10:
                    res += "\\n"
                elif i == 13:
                    res += "\\r"
                else:
                    res += chr(i)
            else:
                if not tag:
                    if len(res) == 0:
                        res += "["
                    else:
                        res += "+["
                    tag = True
                else:
                    res += " "
                hexs = hex(i)[2:].upper()
                if len(hexs) < 2:
                    hexs = "0"+hexs
                res += hexs
        if tag:
            res += "]"
    elif format == "hex":
        for i in data:
            hexs = hex(i)[2:].upper()
            if len(hexs) < 2:
                hexs = "0" + hexs
            res += hexs + " "
        res = res[:-1]
    else:
        tag = False
        tag_time = 0
        for i in data:
            if i in strings:
                tag = False
                tag_time = 0
                if i == 9:
                    res += "\\t"
                elif i == 10:
                    res += "\\n"
                elif i == 13:
                    res += "\\r"
                else:
                    res += chr(i)
            else:
                if not tag:
                    res += "..."
                    tag = True
                else:
                    tag_time += 1
                    if tag_time > 8:
                        res += "..."
                    pass
    return res