#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: I2cylib
# Filename: client
# Created on: 2021/9/29

import threading
import time
import socket
from i2cylib.network.i2tcp_basic.base_client import I2TCPclient
from i2cylib.utils.logger import Logger


class Client(I2TCPclient):

    def __init__(self, hostname, port=24678, key=b"I2TCPbasicKey",
                 watchdog_timeout=15, logger=Logger(),
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

        self.max_buffer = max_buffer_size
        self.package_buffer = []

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

    def connect(self, timeout=10):
        """
        connect to server  连接到I2TCP服务器

        :param timeout: int, connection timeout 设置超时时间
        :return: bool, connection status 连接状态（成功为True）
        """
        super(Client, self).connect(timeout=timeout)

    def send(self, data):
        """
        send data to server 向I2TCP服务器发送数据

        :param data: bytes, data to send (smaller than 16MB) 待发送的数据
        :return: int, total amount of bytes that has been sent 发送出去的总大小
        """
        return super(Client, self).send(data)

    def get(self, header=None, timeout=0):
        """
        get one package with specified header(or not)  从缓冲池中获取数据包（可指定包头部进行筛选）

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
                time.sleep(0.002)
            elif timeout == 0 or (time.time() - t) > timeout:
                break

        return ret

    def connect(self, timeout=10):
        """
        connect to server

        :return: bool, connection status
        """

        if self.connected:
            self.logger.ERROR("{} server has already connected".format(self.log_header))
            return self.connected
        clt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clt.settimeout(timeout)
        try:
            clt.connect(self.address)
        except Exception as err:
            self.logger.ERROR("{} failed to connect to server, {}".format(self.log_header, err))
            return self.connected
        try:
            dynamic_key = self.keygen.keygen()
            clt.sendall(dynamic_key)
            feedback = clt.recv(65536)
            if feedback != b"OK":
                raise Exception("invalid key or invalid server")
            self.clt = clt
            self.live = True
            self.connected = True
            self._start()
        except Exception as err:
            self.logger.ERROR("{} failed to auth, {}".format(self.log_header, err))
            return self.connected
        self.logger.INFO("{} server {}:{} connected".format(self.log_header,
                                                            self.address[0],
                                                            self.address[1]))

        threading.Thread(target=self._receiver_thread).start()

        return self.connected
