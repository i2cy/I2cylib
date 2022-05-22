#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: I2cylib
# Filename: client
# Created on: 2021/9/29

import threading
import time
import rsa
import random
from hashlib import md5
from i2cylib.network.i2tcp_basic import I2TCPclient
from i2cylib.crypto.iccode import Iccode
from i2cylib.utils import random_keygen

VERSION = "2.1"


class Client(I2TCPclient):

    def __init__(self, hostname, port=24678, key=b"I2TCPbasicKey",
                 watchdog_timeout=15, logger=None,
                 max_buffer_size=100):
        """
        I2TCPclient 客户端通讯类

        :param hostname: str, server address 服务器地址
        :param port: int, server port 服务器端口
        :param key: str, dynamic key for authentication 对称动态密钥
        :param watchdog_timeout: int, watchdog timeout 守护线程超时时间
        :param logger: Logger, client log output object 日志器（来自于i2cylib.utils.logger.logger.Logger）
        :param max_buffer_size: int, max pakcage buffer size 最大包缓冲池大小（单位：个）
        """
        super(Client, self).__init__(hostname, port=port, key=key,
                                     watchdog_timeout=watchdog_timeout,
                                     logger=logger)

        self.connection_timeout = 10

        self.max_buffer = max_buffer_size
        self.package_buffer = []

        self.public_key = None
        self.coder_pack = None
        self.coder_depack = None

        self.flag_pack_busy = False
        self.flag_depack_busy = False
        self.flag_secured_connection_built = False

        self.version = VERSION.encode()

    def _packager(self, data):
        """
        【保留】 pack data with I2TCP format

        :param data: bytes
        :return: List(bytes), packed data
        """
        offset = 0
        paks = []
        length = len(data)

        if self.flag_secured_connection_built:  # 安全连接加密
            assert isinstance(self.coder_pack, Iccode)
            while self.flag_pack_busy:
                time.sleep(0.001)
            self.flag_pack_busy = True
            self.coder_pack.reset()
            data = self.coder_pack.encode(data)
            self.flag_pack_busy = False

        left = length
        header_unit = self.version + self.keygen.key
        package_id = bytes((random.randint(0, 255),))
        while left > 0:
            pak = b"A" + left.to_bytes(length=3, byteorder='big', signed=False)
            if left < 8182:
                left = 0
            else:
                left -= 8182
            pak_length = length - left - offset
            pak += pak_length.to_bytes(length=2, byteorder='big', signed=False)
            pak += md5(pak + header_unit).digest()[:3]
            pak += package_id
            pak += data[offset:length - left]
            offset = length - left
            paks.append(pak)
        return paks

    def _check_receiver(self):
        """
        check the receiver and runs it if it is not running

        :return: status
        """
        if not self.threads["receiver"]:
            self.logger.WARNING("{} [checker] receiver thread is not running, restarting")
            threading.Thread(target=self._receiver_thread).start()

    def _receiver_thread(self):
        """
        receiving packages from server and move it to buffer

        :return: None
        """

        self.threads.update({"receiver": True})
        local_header = "[receiver]"
        self.logger.DEBUG("{} {} thread started".format(
            self.log_header, local_header
        ))

        tick = 0

        while self.live:
            package = self.recv(False)

            if self.flag_secured_connection_built:  # 安全连接解密
                assert isinstance(self.coder_depack, Iccode)
                while self.flag_depack_busy and self.live:
                    time.sleep(0.001)
                if package:
                    self.flag_depack_busy = True
                    self.coder_depack.reset()
                    package = self.coder_depack.decode(package)
                    self.flag_depack_busy = False

            if package is not None:
                self.package_buffer.append(package)

            if len(self.package_buffer) > self.max_buffer:
                self.package_buffer.pop(0)
                self.logger.WARNING("{} {} package buffer emitted, packages the oldest may be lost".format(
                    self.log_header, local_header
                ))

            tick += 1

        self.threads.update({"receiver": False})
        self.logger.DEBUG("{} {} thread stopped".format(self.log_header, local_header))

    def reset(self):
        """
        reset I2TCP connection (close connection)  关闭连接

        :return: None
        """
        super(Client, self).reset()
        self.public_key = None
        self.coder_pack = None
        self.coder_depack = None

        self.flag_pack_busy = False
        self.flag_depack_busy = False
        self.flag_secured_connection_built = False
        self.package_buffer = []

    def send(self, data):
        """
        send data to server 向I2TCP服务器发送数据
        it is recommended that data length to be timed by 8182 bytes 推荐单次发送大小位8182的整数倍

        :param data: bytes, data to send (smaller than 16MB) 待发送的数据
        :return: int, total amount of bytes that has been sent 发送出去的总大小
        """
        return super(Client, self).send(data)

    def get(self, header=None, timeout=0):
        """
        get one package with specified header(or not)  从缓冲池中获取数据包（可指定包头部进行筛选）若超时则返回None

        :param timeout: int, timeout for receiving specified header  超时时间
        :param header: bytes, package header  包头部，可不指定
        :return: bytes, depacked data  解析后的包数据（不含协议层）
        """

        ret = None
        t = time.time()
        while ret is None:
            if len(self.package_buffer) > 0:
                for i, ele in enumerate(self.package_buffer):
                    if header is None or ele[:len(header)] == header:
                        got = self.package_buffer.pop(i)
                        ret = got
                        break

            if timeout:
                time.sleep(0.0001)
            if timeout == 0 or (time.time() - t) > timeout:
                break

        return ret

    def connect(self, timeout=10):
        """
        connect to server  连接到I2TCP服务器

        :param timeout: int, connection timeout 设置超时时间
        :return: bool, connection status 连接状态（成功为True）
        """

        if self.connected:
            return
        self.reset()
        ret = super(Client, self).connect(timeout=timeout)
        self.connection_timeout = timeout

        if ret:
            threading.Thread(target=self._receiver_thread).start()

        flag = self.get(timeout=self.connection_timeout)
        if flag is None:
            self.logger.ERROR("{} failed to build connection, flag didn't received".format(
                self.log_header
            ))
            self.connected = False
            self.reset()
            return self.connected

        flag = flag.split(b"\a")

        if flag[0] == b"SECURED_SESSION_KEY_REQUIRED":
            try:
                self.public_key = rsa.PublicKey.load_pkcs1(flag[1])
                self.logger.DEBUG("{} public rsa key received, \n{}".format(self.log_header, flag[1].decode()))
            except Exception as err:
                self.logger.ERROR("{} broken rsa key received, {}".format(self.log_header, flag[1]))
                self.connected = False
                self.reset()
                return self.connected

            try:
                session_key = random_keygen(64)
                self.coder_pack = Iccode(session_key, fingerprint_level=3)
                self.coder_depack = Iccode(session_key, fingerprint_level=3)
                self.logger.DEBUG("{} random session key generated: {}".format(self.log_header, session_key))
                session_key = rsa.encrypt(session_key, self.public_key)

                self.send(session_key)

            except Exception as err:
                self.logger.ERROR("{} error while sending session key to server, {}".format(
                    self.log_header, err
                ))
                self.connected = False
                self.reset()
                return self.connected

            feedback = self.get(timeout=self.connection_timeout)
            if feedback != b"CODER READY":
                self.logger.ERROR("{} error while waiting ready signal from server".format(
                    self.log_header
                ))
                self.connected = False
                self.reset()
                return self.connected

            self.logger.DEBUG("{} secured connection built".format(self.log_header))
            self.flag_secured_connection_built = True

        elif flag[0] == b"AUTHENTICATION_ONLY":
            self.logger.DEBUG("{} connection built".format(self.log_header))

        else:
            self.logger.ERROR("{} failed to build connection, unexpected flag received, {}".format(
                self.log_header, flag
            ))
            self.connected = False
            self.reset()
            return self.connected
