#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: icen.py
# Filename: operators
# Created on: 2022/1/28

import hashlib


def hash_compare(val1, val2):
    hasher_1 = hashlib.sha256()
    hasher_2 = hashlib.sha256()
    hasher_1.update(val1)
    hasher_2.update(val2)

    return hasher_1.digest() == hasher_2.digest()


if __name__ == '__main__':
    import time
    ts = time.time()
    res = hash_compare(b"123" * 1024 * 100, b"1234" * 1024 * 128)
    t = time.time() - ts
    print("hash_compare 123 and 1234: {}, time spend: {} us".format(res, t*10**6))
    ts = time.time()
    res = hash_compare(b"abcd" * 1024 * 128, b"abcd" * 1024 * 128)
    t = time.time() - ts
    print("hash_compare abcd and abcd: {}, time spend: {} us".format(res, t * 10 ** 6))
