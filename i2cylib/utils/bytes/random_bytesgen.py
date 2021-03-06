# -*- coding: utf-8 -*-
# Author: Icy(i2cy@outlook.com)
# OS: ALL
# Name: Random Bytes Generator
##VERSION: 0.0.1

import random

def random_keygen(length): # random bytes generator
    res = []
    for i in range(length):
        res.append(int(random.random()*255))
    return bytes(res)