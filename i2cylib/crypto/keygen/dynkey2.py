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

    def __init__(self, key, flush_times=1, divide=60, key_buff_max=5):
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
        self.__key_buff_max = key_buff_max
        self.__key_buffer = []

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

    def keygen(self, offset=0):  # 16-Bytes dynamic key generator
        timestamp = int(time.time() / self.divide) + int(offset)

        # search for the key that previously generated
        key = self.__find_buffed(timestamp)
        if key != b"":
            return key

        # generate new if it doesn't exists
        key_unit = md5(self.key).digest()
        sub_key_unit = list(md5(timestamp.to_bytes(4, "little", signed=False)).digest())
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

        ret = bytes(sub_key_unit)
        self.__key_buffer.append([timestamp, ret])
        self.__buffer_check()

        return ret

    def keymatch(self, key):  # Live key matcher
        lock = [self.keygen(offset) for offset in range(-1, 2)]
        if key in lock:
            return True
        else:
            return False


if __name__ == '__main__':
    kg = DynKey16(b"testtest123", flush_times=2)
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
