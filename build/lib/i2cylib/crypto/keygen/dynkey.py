# -*- coding: utf-8 -*-
# Author: I2cy(i2cy@outlook.com)
# OS: ALL
# Name: time based dynamic key generator/matcher
# Description: This function is used for socket package auth
# Used Librarie(s): time, hashlib
# Version: 1.0

import time
from hashlib import md5

class dynKey: # 64-Bits dynamic key generator/matcher

    def __init__(self, key, flush_times=1, multiplier=0.01):
        if isinstance(key, str):
            key = key.encode()
        elif isinstance(key, bytes):
            pass
        else:
            raise Exception("private key must be String or Bytes")
        self.key = key
        self.multiplier = multiplier
        if flush_times <= 0:
            flush_times = 1
        self.flush_time = flush_times


    def keygen(self, offset=0): # 64-Bits dynamic key generator
        time_unit = int(time.time() * self.multiplier) + int(offset)
        time_unit = str(time_unit).encode()
        time_unit = md5(time_unit).digest()
        key_unit = md5(self.key).digest()
        sub_key_unit = time_unit + key_unit

        for i in range(self.flush_time):
            sub_key_unit = md5(sub_key_unit).digest()[::-1]
            conv_core = [int((num + 1*self.multiplier) % 255 + 1) for num in sub_key_unit[:3]]
            conv_res = []
            for i2, ele in enumerate(sub_key_unit[3:-2]):
                conv_res_temp = 0
                for c in range(3):
                    conv_res_temp += sub_key_unit[3+i2+c] * conv_core[c]
                conv_res.append(int(conv_res_temp%256))
            sub_key_unit = md5(sub_key_unit[:3] + bytes(conv_core)).digest()[::-1]
            sub_key_unit += md5(sub_key_unit + bytes(conv_res)).digest()
            sub_key_unit += md5(bytes(conv_res)).digest()
            sub_key_unit += md5(bytes(conv_res) + self.key).digest()
            sub_key_unit += key_unit

        conv_cores = [[time_unit[i2] for i2 in range(4*i, 4*i+4)]
                      for i in range(4)]

        for i, ele in enumerate(conv_cores):
            ele.insert(2, 1*self.multiplier + (key_unit[i] + key_unit[i+4] + key_unit[i+8] + key_unit[i+12]) // 4)

        final_key = sub_key_unit

        for i in range(4):
            conv_core = conv_cores[i]
            conv_res = []
            for i2, ele in enumerate(final_key[:-4]):
                conv_res_temp = 0
                for c in range(5):
                    conv_res_temp += final_key[i2+c] * conv_core[c]
                conv_res.append(int(conv_res_temp%256))
            final_key = bytes(conv_res)

        return final_key

    def keymatch(self, key): # Live key matcher
        lock_1 = self.keygen(-1)
        lock_2 = self.keygen(0)
        lock_3 = self.keygen(1)
        lock = [lock_1,lock_2,lock_3]
        if key in lock:
            return True
        else:
            return False