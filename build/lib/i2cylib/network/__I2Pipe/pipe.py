#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: I2cyLib
# Filename: pipe
# Created on: 2022/2/5

import os.path
from i2cylib.utils.stdout.echo import Echo
from i2cylib.network.I2TCP.server import *
from i2cylib.network.I2TCP.client import *
import rsa

RSA_PRIVATE_KEY = None
RSA_PUBLIC_KEY = None

LOGGER = Logger()


def init_pipe():
    global RSA_PUBLIC_KEY
    global RSA_PRIVATE_KEY
    global LOGGER
    log_head = "[init]"
    # 检查缓存路径状态
    if not os.path.exists(os.path.expanduser(".i2local/")):
        os.makedirs(os.path.expanduser(".i2local/"))
    LOGGER = Logger(os.makedirs(os.path.expanduser(".i2local/pipe.log")))
    LOGGER.INFO("{} initializing profile".format(log_head))
    try:
        # 加载RSA公钥
        with open(os.path.expanduser(".i2local/pipe_public.pem"), "rb") as f:
            RSA_PUBLIC_KEY = rsa.PublicKey.load_pkcs1(f.read())
            f.close()
        # 加载RSA私钥
        with open(os.path.expanduser(".i2local/pipe_private.pem"), "rb") as f:
            RSA_PRIVATE_KEY = rsa.PrivateKey.load_pkcs1(f.read())
            f.close()
        LOGGER.INFO("{} loaded rsa key chain")
    except:
        LOGGER.INFO("{} generating new RSA-2048 key chain")
