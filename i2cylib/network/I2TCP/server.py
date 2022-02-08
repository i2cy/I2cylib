#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: I2cylib
# Filename: server
# Created on: 2021/9/29


import time
from i2cylib.network.i2tcp_basic import I2TCPserver, I2TCPhandler
from i2cylib.utils.logger import Logger


class Server(I2TCPserver):

    def __init__(self, key=b"I2TCPbasicKey", port=24678,
                 max_con=20, logger=None):
        """
        I2TCP server class  I2TCP服务端类

        :param key: str(or bytes), dynamic key for authentication  对称动态密钥
        :param port: int, server port that to be bond  服务端要绑定的端口号
        :param max_con: int, max TCP connection(s) that allowed
                        to be accept at the same time  最大同时接受的连接数
        :param logger: Logger, server log output object  日志器（来自于i2cylib.utils.logger.logger.Logger）
        """
        super(Server, self).__init__(key=key, port=port, max_con=max_con,
                                     logger=logger)

    def _mainloop_thread(self):
        """
        over write server main loop

        :return: None
        """

        self.threads.update({"mainloop": True})
        local_header = "[mainloop]"
        self.logger.DEBUG("{} {} thread started".format(self.log_header, local_header))

        try:
            while self.live:
                con, addr = self.srv.accept()
                if self.live:
                    self.logger.INFO("{} new connection {}:{} coming in".format(self.log_header,
                                                                                addr[0], addr[1]))
                    handler = Handler(con, addr, self)
                    for i in range(self.max_con):
                        if self.connections[i] is None:
                            self.connections.update({i: {"handler": handler,
                                                         "handled": False}})
                            break
                else:
                    break

        except Exception as err:
            self.logger.ERROR("{} {} mainloop error, {}".format(self.log_header, local_header, err))

        self.logger.DEBUG("{} {} thread stopped".format(self.log_header, local_header))
        self.threads.update({"mainloop": False})

    def start(self, port=None):
        """
        start I2TCP server  启动I2TCP服务端并开始监听端口
        
        :param port: int or None, leave it empty to use self.port  选择端口，默认self.port
        :return: None
        """
        super(Server, self).start(port=port)
    
    def kill(self):
        """
        kill I2TCP server  关闭I2TCP服务端
        
        :return: None
        """
        super(Server, self).kill()
    
    def get_connection(self, wait=False):
        """
        get one connection that yet to be handled  获取一个尚未被接手的连接
        
        :param wait: bool, should we wait or not until we got a connection  是否阻塞
        :return: Handler, connection handler  连接处理类
        """
        return super(Server, self).get_connection(wait=wait)


class Handler(I2TCPhandler):

    def __init__(self, srv, addr, parent, timeout=20,
                 buffer_max=256, watchdog_timeout=15, temp_dir="temp"):
        super(Handler, self).__init__(srv, addr, parent, timeout=20,
                                      buffer_max=256, watchdog_timeout=15, temp_dir="temp")

    def kill(self):
        """
        kill this connection  关闭这个连接

        :return: None
        """
        super(Handler, self).kill()

    def send(self, data):
        """
        send data to client  向客户端发送数据

        :param data: bytes, data to send (smaller than 16MB) 待发送的数据
        :return: int, total amount of bytes that has been sent 发送出去的总大小
        """
        return super(Handler, self).send(data)

    def get(self, header=None, timeout=0):
        """
        receive a whole package from client  获得一个来自客户端的数据包

        :param header: bytes, package header to get the specified package  包头部，可不选
        :param timeout: int (default: 0), timeout for not receiving data from client  超时
        :return: bytes, depacked data  解包后的数据
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
