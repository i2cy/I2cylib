#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: I2cylib
# Filename: test
# Created on: 2021/9/30

from i2cylib.network.I2TCP.client import Client
from i2cylib.network.I2TCP.server import Server, Handler
from i2cylib.utils.logger.logger import Logger
from hashlib import sha512
import random
import threading


def massive_send(clt, data):
    assert isinstance(clt, Client)

    clt.send(data)


if __name__ == '__main__':
    logger = Logger()
    srv = Server(port=24678, key=b"test", logger=logger)
    clt = Client(port=24678, hostname="127.0.0.1", key=b"test", logger=logger)

    srv.start()
    clt.connect()

    data = b""

    for i in range(1024*32):
        data += bytes((int(256*random.random()),))

    for i in range(16):
        threading.Thread(target=massive_send, args=(clt, "A{}".format(i).encode() + data)).start()

    hasher_1 = sha512()
    hasher_1.update(data)

    srv_clt = srv.get_connection()

    assert isinstance(srv_clt, Handler)

    while True:
        data_recv = srv_clt.get(b"A15")
        if data_recv is not None:
            break

    data_recv = data_recv[3:]

    hasher_2 = sha512()
    hasher_2.update(data_recv)

    logger.INFO("[main] data transition result: {}".format(hasher_2.digest() == hasher_1.digest()))

    clt.reset()
    srv.kill()
