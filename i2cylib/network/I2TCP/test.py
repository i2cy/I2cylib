#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: I2cylib
# Filename: test
# Created on: 2021/9/30

from client import Client
from server import Server, Handler
from i2cylib.utils.logger import Logger
from hashlib import sha512
import random
import time
import threading


def massive_send(clt, data):
    assert isinstance(clt, Client)

    clt.send(data)


if __name__ == '__main__':
    logger = Logger()
    srv = Server(port=24678, key=b"test", logger=logger, secured_connection=False)
    clt = Client(port=24678, hostname="127.0.0.1", key=b"test", logger=logger)

    srv.start()
    clt.connect()

    data = b""

    logger.INFO("[main] generating random data to send")
    for i in range(1024*256):
        data += bytes((int(256*random.random()),))

    for i in range(16):
        threading.Thread(target=massive_send, args=(clt, "A{}".format(i).encode() + data)).start()

    hasher_1 = sha512()
    hasher_1.update(data)

    srv_clt = srv.get_connection(wait=True)

    assert isinstance(srv_clt, Handler)

    time.sleep(2)

    data_recv_nohead = srv_clt.get(timeout=3)
    data_recv = srv_clt.get(b"A15", timeout=3)

    logger.INFO("[main] data with head {} received".format(data_recv_nohead[:3]))

    logger.INFO("[main] data with head {} has been got (arg=b\"A15\")".format(data_recv[:3]))

    data_recv = data_recv[3:]
    data_recv_nohead = data_recv_nohead[3:]

    hasher_2 = sha512()
    hasher_2.update(data_recv)

    data = data * 4
    time_spend_avg = 0

    for i in range(200):
        ts = time.time()
        clt.send(data)
        rs = time.time() - ts
        time_spend_avg += rs / 200

    clt.reset()
    srv.kill()

    logger.INFO("[main] data transition result: {}".format(hasher_2.digest() == hasher_1.digest()))
    logger.INFO("[main] speed test result: {:.4f} MB/s".format((len(data) / 1024 / 1024) / time_spend_avg))
