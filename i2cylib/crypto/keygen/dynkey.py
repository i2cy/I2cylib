# -*- coding: utf-8 -*-
# Author: I2cy(i2cy@outlook.com)
# OS: ALL
# Name: time based dynamic key generator/matcher
# Description: This function is used for socket package auth
# Used Librarie(s): time, hashlib

import time
from hashlib import md5
from typing import Any, Tuple

__VERSION__ = 1.1


class DynKey:  # 64-Bits dynamic key generator/matcher

    def __init__(self, key, flush_times: int = 1, multiplier: float = 0.01,
                 key_buff_max: int = 5):
        """
        64-Bits dynamic key generator/matcher
        :param key: basic pre-shared key
        :param flush_times: generator salts
        :param multiplier: scale factor of timestamp, the
        :param key_buff_max:
        """
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
        self.__debug = False
        self.__key_buff_max = key_buff_max
        self.__key_buffer = []

    def switchDebug(self):
        self.__debug = not self.__debug
        return self.__debug

    def __buffer_check(self):
        """
        this is a private function that meant to be limiting the key buffer length
        :return:
        """
        if len(self.__key_buffer) > self.__key_buff_max:
            self.__key_buffer.sort()
            self.__key_buffer = self.__key_buffer[len(self.__key_buffer) - self.__key_buff_max:]

    def __find_buffed(self, time_unit) -> bytes:
        """
        find and return cached key if time unit is cached
        :return: key array in bytes
        """
        ret = b""
        for tu, key in self.__key_buffer[::-1]:
            if time_unit == tu:
                ret = key
                break
        return ret

    def keygen(self, offset=0):  # 64-Bits dynamic key generator
        time_unit_raw = int(time.time() * self.multiplier) + int(offset)

        # search for the key that previously generated
        key = self.__find_buffed(time_unit_raw)
        if key != b"":
            return key

        # generate new if it doesn't exists
        time_unit = str(time_unit_raw).encode()
        time_unit = md5(time_unit).digest()
        key_unit = md5(self.key).digest()
        sub_key_unit = time_unit + key_unit

        for i in range(self.flush_time):
            sub_key_unit = md5(sub_key_unit).digest()[::-1]
            conv_core = [int((num + 1 * self.multiplier) % 255 + 1) for num in sub_key_unit[:3]]
            conv_res = []
            for i2, ele in enumerate(sub_key_unit[3:-2]):
                conv_res_temp = 0
                for c in range(3):
                    conv_res_temp += sub_key_unit[3 + i2 + c] * conv_core[c]
                conv_res.append(int(conv_res_temp % 256))
            sub_key_unit = md5(sub_key_unit[:3] + bytes(conv_core)).digest()[::-1]
            sub_key_unit += md5(sub_key_unit + bytes(conv_res)).digest()
            sub_key_unit += md5(bytes(conv_res)).digest()
            sub_key_unit += md5(bytes(conv_res) + self.key).digest()
            sub_key_unit += key_unit

        conv_cores = [[time_unit[i2] for i2 in range(4 * i, 4 * i + 4)]
                      for i in range(4)]

        for i, ele in enumerate(conv_cores):
            ele.insert(2,
                       1 * self.multiplier + (key_unit[i] + key_unit[i + 4] + key_unit[i + 8] + key_unit[i + 12]) // 4)

        final_key = sub_key_unit

        for i in range(4):
            conv_core = conv_cores[i]
            conv_res = []
            for i2, ele in enumerate(final_key[:-4]):
                conv_res_temp = 0
                for c in range(5):
                    conv_res_temp += final_key[i2 + c] * conv_core[c]
                conv_res.append(int(conv_res_temp % 256))
            final_key = bytes(conv_res)
            if self.__debug:
                print("Conv2, iter {}: length {}".format(i, len(final_key)))

        self.__key_buffer.append([time_unit_raw, final_key])
        self.__buffer_check()

        return final_key

    def keymatch(self, key):  # Live key matcher
        lock = [self.keygen(offset) for offset in range(-1, 2)]
        if key in lock:
            return True
        else:
            return False


if __name__ == '__main__':
    kg = DynKey(b"testtest123")
    kg.switchDebug()
    a = kg.keygen()
    print("key match:", kg.keymatch(a))
