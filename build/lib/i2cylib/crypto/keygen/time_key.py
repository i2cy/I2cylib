# -*- coding: utf-8 -*-
# Author: Icy(enderman1024@foxmail.com)
# OS: ALL
# Name: Time key generator/matcher
# Description: This function is used for socket server
# Used Librarie(s): time
# Version: 1.2

import time

class timeKey: # 64-Bits Live key generator/matcher
    def __init__(self,key):
        if type(key) != type(""):
            raise Exception("key must be a string")
        self.key = key
    def keygen(self,mt=0): # 64-Bits Live key generator
        dt = int(str(int(time.time()))[:-2]) + mt
        sub_key_unit = str(int(str(4*dt**8 + 8*dt**4 + 2*dt**2 + 4*dt + 1024)[::-1]) + 3*dt**4 + 2*dt**3 + 3*dt**2 + 2*dt)
        final_key = b""
        n = 0
        n2 = 0
        for i in range(64):
            if n == len(sub_key_unit):
                n = 0
            if n2 == len(self.key):
                n2 = 0
            final_key_unit = ord(self.key[n2]) + ord(sub_key_unit[n])
            if final_key_unit >= 255:
                final_key_unit -= 256
            final_key += bytes((final_key_unit,))
            n += 1
            n2 += 1
        return final_key
    def keymatch(self,key): # Live key matcher
        lock_1 = self.keygen(-1)
        lock_2 = self.keygen(0)
        lock_3 = self.keygen(1)
        lock = [lock_1,lock_2,lock_3]
        if key in lock:
            return True
        else:
            return False
