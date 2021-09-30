#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: I2cylib
# Filename: iccode
# Created on: 2021/9/25


from hashlib import sha512
import numpy as np


class Iccode:  # Simple Data Encoder/Decoder

    def __init__(self, base_key, fingerprint_level=3):
        """
        ICCode Simple Data Encryptor

        :param base_key: str (or bytes), basic key for encryptor
        :param fingerprint_level: int (>=1), encryption level, higher for more security
        """

        if len(base_key) <= 1:
            raise Exception("'base_key' length must be greater than 1")
        if not isinstance(base_key, bytes):
            try:
                base_key = base_key.encode()
            except Exception as err:
                raise Exception("can not encode \"base_key\"")

        self.__version__ = "3.0.0"

        self.base_key = self.generate_key(base_key)
        self.buffer_key = self.base_key.copy()
        self.block_length = len(self.base_key)
        self.fingerprint_level = fingerprint_level
        self.step = 0

    def sign_key(self, key):
        """
        generate a fingerprint from given key

        :param key: np.ndarray (or bytes)
        :return: np.ndarray, length 1024 bytes
        """
        if isinstance(key, bytes):
            ret = np.frombuffer(key, dtype=np.uint8)
        else:
            ret = key.copy()

        ret += self.base_key

        for i in range(1, self.fingerprint_level):
            ret += np.power(ret, i + 1)

        return ret

    def generate_key(self, key):
        """
        generate a sha512 key

        :param key: bytes
        :return: bytes, 1024 bytes
        """
        ret = key

        for i in range(16):
            coder = sha512()
            coder.update(ret)
            ret += coder.digest()

        ret = np.frombuffer(ret[len(key):], dtype=np.uint8)

        return ret

    def reset(self, key=None):  # reset coder
        """
        reset coder sum

        :return: None
        """

        self.step = 0

        if key is None:
            self.buffer_key = self.base_key.copy()
        else:
            self.buffer_key = self.generate_key(key)

    def encode(self, data):  # encoder
        """
        encode data with buffer and base key

        :param data: bytes, length of 1024*n is the best
        :return: bytes, encoded bytes
        """

        res = b""
        if not len(data):
            return b""
        fill_size_a = self.step % 1024
        fill_size_b = 0
        if fill_size_a:
            data = b"\x00" * fill_size_a + data
        if len(data) % 1024:
            fill_size_b = (1024 - (len(data) % 1024)) % 1024
            data += fill_size_b * b"\x00"

        for i in range(len(data) // 1024):
            tmp = np.frombuffer(data[1024 * i: 1024 * (i + 1)], dtype=np.uint8)
            res += (tmp + self.sign_key(self.buffer_key)).tobytes()

            self.buffer_key = self.buffer_key + (tmp * self.base_key)

            if self.step % 1024:
                self.step += 1024 - fill_size_a
            else:
                self.step += 1024

        if fill_size_a or fill_size_b:
            res = res[fill_size_a:len(res) - fill_size_b]
            self.step -= fill_size_b

        return res

    def decode(self, data):  # decoder
        """
        decode data with buffer and base key

        :param data: bytes, length of 1024*n is the best
        :return: bytes, decoded bytes
        """

        res = b""
        if not len(data):
            return b""
        fill_size_a = self.step % 1024
        fill_size_b = 0
        if fill_size_a:
            data = b"\x00" * fill_size_a + data
        if len(data) % 1024:
            fill_size_b = (1024 - (len(data) % 1024)) % 1024
            data += fill_size_b * b"\x00"

        for i in range(len(data) // 1024):
            tmp = np.frombuffer(data[1024 * i: 1024 * (i + 1)], dtype=np.uint8)

            tmp = tmp - self.sign_key(self.buffer_key)
            res += tmp.tobytes()

            if self.step % 1024:
                self.buffer_key = self.buffer_key + \
                                  np.concatenate((np.zeros((fill_size_a,), dtype=np.uint8),
                                                  (tmp * self.base_key)[fill_size_a:]))
                self.step += 1024 - fill_size_a
            else:
                self.buffer_key = self.buffer_key + (tmp * self.base_key)
                self.step += 1024

        if fill_size_a or fill_size_b:
            res = res[fill_size_a:len(res) - fill_size_b]
            self.step -= fill_size_b
            self.buffer_key = self.buffer_key - \
                              np.concatenate((np.zeros((1024 - fill_size_b,), dtype=np.uint8),
                                              (tmp * self.base_key)[1024 - fill_size_b:]))

        return res


if __name__ == '__main__':
    import time
    import random
    import os

    coder = Iccode(b"test", 2)
    print("key generated: \n{}".format(coder.base_key))
    source = b"H"

    if not os.path.exists("test.data"):
        with open("test.data", "wb") as f:
            for i in range(1024 * 1024 * 10):
                f.write(bytes((int(256 * random.random()),)))
            f.close()
    t = time.time()
    source_encoded = b""

    print("speed test, encoding 20MB bytes...")
    for i in range(1024 * 10):
        coder.encode(source * 2048)
    res = time.time() - t
    print("time spent: {:.1f}s , speed {:.2f} MB/s".format(res, 20 / res))
    print("data encoded header: {}".format(source_encoded[0:64]))

    coder.reset()
    t = time.time()
    print("speed test, decoding 20MB bytes...")
    for i in range(1024 * 10):
        coder.decode(source * 2048)
    res = time.time() - t
    print("time spent: {:.1f}s , speed {:.2f} MB/s".format(res, 20 / res))

    f = open("test.data", "rb")
    encoded_f = open("test_encoded.data", "wb")

    print("testing data encryption accuracy")
    coder.reset()

    print("encrypting...")
    hasher = sha512()
    while True:
        tmp = f.read(int(random.random() * 5000 + 1))
        if tmp == b"":
            break
        hasher.update(tmp)
        encoded_f.write(coder.encode(tmp))

    f.close()
    encoded_f.close()

    hash_code = hasher.digest()

    hasher = sha512()
    encoded_f = open("test_encoded.data", "rb")

    coder.reset()

    print("decrypting...")

    while True:
        tmp = encoded_f.read(int(random.random() * 5000 + 1))

        if tmp == b"":
            break

        res = coder.decode(tmp)
        hasher.update(res)

    print("test result: {}".format(hash_code == hasher.digest()))
