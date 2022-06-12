#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: I2cyLib
# Filename: htsocket
# Created on: 2022/5/31
import time

import serial
from i2cylib.utils.logger.logger import *


class HTSocket:

    def __init__(self, port="/dev/ttyTHS1", baudrate=115200, head=b"\xaa",
                 timeout=5):
        """
        HT Serial Socket Protocol

        :param port: int
        :param baudrate: int
        :param head: bytes
        :param timeout: int
        """

        self.head = head
        self.baudrate = baudrate
        self.port = port
        self.client = None
        self.timeout = timeout
        self.__lock = False

    def connect(self, port=None, baudrate=None, timeout=None):
        """
        connect to the target

        :param port: int or None
        :param baudrate: int or None
        :param timeout: int or None
        :return: None
        """
        if port is not None:
            self.port = port
        if baudrate is not None:
            self.baudrate = baudrate
        if timeout is not None:
            self.timeout = timeout

        self.client = serial.Serial(self.port, self.baudrate, timeout=self.timeout)

    def __pack(self, addr, data, send_length):
        if isinstance(addr, int):
            addr = bytes((addr,))

        ret = self.head
        ret += addr
        if send_length:
            ret += bytes((len(data),))
        ret += data
        sum_v = sum(ret) % 256
        ret += bytes((sum_v,))

        return ret

    def __depack(self, header, data):
        if len(data) == 0:
            return False, 0
        sum_v = sum(header + data[:-1]) % 256
        if sum_v != data[-1]:
            return False, sum_v
        else:
            return True, data[:-1]

    def send(self, addr, data, send_length=True, check=False):
        """
        serial send function

        :param addr: bytes,
        :param data: bytes,
            total length is no more than 256
        :param send_length: bool (default=True).
            whether include data length or not
        :param check: bool,
            wait for OK flag
        :return: int, frame length that has been sent
        """
        if not isinstance(self.client, serial.Serial):
            raise ConnectionError("no connection built yet")

        if not isinstance(addr, bytes):
            raise Exception("address must be bytes")
        if len(data) >= 256:
            raise Exception("data length must be less than 256")

        t = time.time()
        ret = None
        data = self.__pack(addr, data, send_length=send_length)

        # print(data)

        while self.__lock:
            time.sleep(0.001)
        self.__lock = True

        while True:
            ret = self.client.write(data)

            if check:
                if time.time() - t > 2 * self.timeout:
                    ret = False
                    break
                fb = self.client.read(2)
                if fb == b"OK":
                    break
            else:
                break

            time.sleep(0.05)

        self.__lock = False

        return ret

    def recv(self, addr, length=None):
        """
        serial receive function

        :param addr: bytes
        :param length: None or int.
            length means the total length of data, header and sum are excluded
        :return: data: bytes (headers and sum are excluded)
        """
        if not isinstance(self.client, serial.Serial):
            raise ConnectionError("no connection built yet")

        t = time.time()

        while True:
            if time.time() - t > 2 * self.timeout:
                raise TimeoutError("timeout")

            # print('recving')

            head = self.client.read(1)
            if head != b"\xaa":
                continue

            addr_raw = self.client.read(len(addr))
            if addr_raw != addr:
                continue

            header = head + addr_raw

            # print(header)

            if length is None:
                length = self.client.read(1)
                header += length
                length = int.from_bytes(length, "little", signed=False)
                # print("length {}".format(length))

            t = time.time()
            data_raw = b""
            while time.time() - t < 1 * self.timeout:
                if len(data_raw) == length + 1:
                    break
                data_raw += self.client.read(length + 1 - len(data_raw))

            status, data = self.__depack(header, data_raw)

            if not status:
                continue

            return data

    def close(self):
        if not isinstance(self.client, serial.Serial):
            raise ConnectionError("no connection built yet")

        self.client.close()
        self.client = None


if __name__ == '__main__':
    pass
