#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: I2cylib
# Filename: dynkey2
# Created on: 2022/8/21


from hashlib import md5
import time


class DynKey16:  # 16-Bytes dynamic key generator/matcher
    """
    Added ARM support with more efficient hash algorithm
    """

    def __init__(self, key, flush_times=1, divide=60):
        if isinstance(key, str):
            key = key.encode()
        elif isinstance(key, bytes):
            pass
        else:
            raise Exception("private key must be String or Bytes")
        self.key = key
        self.divide = divide
        if flush_times <= 0:
            flush_times = 1
        self.flush_time = flush_times

    def keygen(self, offset=0):  # 16-Bytes dynamic key generator
        key_unit = md5(self.key).digest()
        timestamp = int(time.time() / self.divide) + int(offset)
        sub_key_unit = list(md5(timestamp.to_bytes(4, "big", signed=False)).digest())
        sub_key_unit = list(md5(bytes(sub_key_unit) + key_unit).digest())

        for i in range(self.flush_time):
            sub_key_unit = list(md5(bytes(sub_key_unit)).digest()[::-1])
            conv_core = []
            for num in sub_key_unit[:3]:
                t = (num + (num % 32) // (self.divide % 4 + 1)) % 255 + 1
                conv_core.append(t)

            for i2, ele in enumerate(sub_key_unit[3:-2]):
                conv_res_temp = 0
                for c in range(3):
                    conv_res_temp += sub_key_unit[3 + i2 + c] * conv_core[c]
                sub_key_unit[3 + i2] = int(conv_res_temp % 256)
            sub_key_unit = list(md5(bytes(sub_key_unit) + bytes(conv_core) + key_unit).digest())

        return bytes(sub_key_unit)

    def keymatch(self, key):  # Live key matcher
        lock_1 = self.keygen(-1)
        lock_2 = self.keygen(0)
        lock_3 = self.keygen(1)
        lock = [lock_1, lock_2, lock_3]
        if key in lock:
            return True
        else:
            return False


if __name__ == '__main__':
    kg = DynKey16(b"testtest123")
    test_match = kg.keygen(-1)
    mea = sum(test_match) / len(test_match)
    print("key length: {}".format(len(test_match)))
    print("test key mean: {}".format(mea))
    f = open("test.txt", "w")
    mea = 0
    for i in range(43200):
        t = kg.keygen(i)
        mea += sum(t) / (len(t) * 43200)
        if t == test_match:
            print("leak detected at offset {}".format(i))
        f.write(t.hex() + "\n")
    print("all key mean: {}".format(mea))
    f.close()
