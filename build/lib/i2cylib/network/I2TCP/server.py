#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: I2cylib
# Filename: server
# Created on: 2021/9/29


import time
import rsa
import random
from hashlib import md5
from i2cylib.network.i2tcp_basic import I2TCPserver, I2TCPhandler
from i2cylib.crypto.iccode import Iccode


VERSION = "2.1"


class Server(I2TCPserver):

    def __init__(self, key=b"I2TCPbasicKey", port=24678,
                 max_con=20, logger=None, secured_connection=True,
                 max_buffer_size=100, watchdog_timeout=15, timeout=20):
        """
        I2TCP server class  I2TCP服务端类

        :param key: str(or bytes), dynamic key for authentication  对称动态密钥
        :param port: int, server port that to be bonded  服务端要绑定的端口号
        :param max_con: int, max TCP connection(s) that allowed
                        to be accepted at the same time  最大同时接受的连接数
        :param logger: Logger, server log output object  日志器（来自于i2cylib.utils.logger.logger.Logger）
        :param secured_connection: bool, enable encryption in connection  启用安全加密层
        :param max_buffer_size: int, max package buffer size for every handler  包缓冲区最大大小（单位：个）
        :param watchdog_timeout: int, timeout value for watchdogs  看门狗超时时间
        :param timeout: int, timeout value for connection  连接超时时间
        """
        super(Server, self).__init__(key=key, port=port, max_con=max_con,
                                     logger=logger)

        self.version = VERSION.encode()

        self.public_key = None
        self.private_key = None
        self.secured_connection = secured_connection

        self.max_buffer_size = max_buffer_size
        self.watchdog_timeout = watchdog_timeout
        self.timeout = timeout

        if secured_connection:
            self.logger.INFO("{} generating secured session RSA keychain".format(self.log_header))
            keys = rsa.newkeys(1024)
            self.private_key = keys[1]
            self.public_key = keys[0]

    def _mainloop_thread(self):
        """
        overwrite server main loop

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
                    handler = Handler(con, addr, self,
                                      timeout=self.timeout, watchdog_timeout=self.watchdog_timeout,
                                      buffer_max=self.max_buffer_size)
                    for i in range(self.max_con):
                        if self.connections[i] is None:
                            self.connections.update({i: {"handler": handler,
                                                         "handled": False}})
                            break
                else:
                    break

        except Exception as err:
            if self.live:
                self.logger.ERROR("{} {} mainloop error, {}".format(self.log_header, local_header, err))

        self.logger.DEBUG("{} {} thread stopped".format(self.log_header, local_header))
        self.threads.update({"mainloop": False})

    def start(self, port=None):
        """
        start I2TCP server  启动I2TCP服务端并开始监听端口
        
        :param port: int or None, leave it empty to use self.port  选择端口，默认self.port
        :return: None
        """
        return super(Server, self).start(port=port)
    
    def kill(self):
        """
        kill I2TCP server  关闭I2TCP服务端
        
        :return: None
        """
        return super(Server, self).kill()
    
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

        self.connection_timeout = timeout
        self.public_key = None
        self.coder_pack = None
        self.coder_depack = None

        self.flag_pack_busy = False
        self.flag_depack_busy = False
        self.flag_secured_connection_built = False

        super(Handler, self).__init__(srv, addr, parent, timeout=timeout,
                                      buffer_max=buffer_max, watchdog_timeout=watchdog_timeout,
                                      temp_dir=temp_dir)

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
            while self.flag_pack_busy and self.live:
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
            if left < 32758:
                left = 0
            else:
                left -= 32758
            pak_length = length - left - offset
            pak += pak_length.to_bytes(length=2, byteorder='big', signed=False)
            pak += bytes((md5(pak + header_unit).digest()[2],))
            payload_sum = md5(data[offset:length - left]).digest()[:2]
            pak += payload_sum
            pak += package_id
            pak += data[offset:length - left]
            offset = length - left
            paks.append(pak)
        return paks

    def _recv(self):
        data = super(Handler, self)._recv()

        if self.flag_secured_connection_built:  # 安全连接解密
            assert isinstance(self.coder_depack, Iccode)
            while self.flag_depack_busy and self.live:
                time.sleep(0.001)
            if data:
                self.flag_depack_busy = True
                self.coder_depack.reset()
                data = self.coder_depack.decode(data)
                self.flag_depack_busy = False

        return data

    def _auth(self):
        ret = super(Handler, self)._auth()

        if not ret:
            return ret
        else:
            self._start()

        if self.parent.secured_connection:
            self.send(b"SECURED_SESSION_KEY_REQUIRED\a" + self.parent.public_key.save_pkcs1("PEM"))
            session_key = self.get(timeout=self.connection_timeout)
            if session_key is None:
                self.logger.ERROR("{} failed to create secured session, connection denied".format(self.log_header))
                return False

            try:
                session_key = rsa.decrypt(session_key, self.parent.private_key)
            except Exception as err:
                self.logger.ERROR("{} failed to decrypt session key from client, {}".format(self.log_header, err))
                return False
            self.logger.DEBUG("{} session key received: {}".format(self.log_header, session_key))
            self.coder_pack = Iccode(session_key, fingerprint_level=3)
            self.coder_depack = Iccode(session_key, fingerprint_level=3)
            self.logger.DEBUG("{} secured connection built".format(self.log_header))
            self.send(b"CODER READY")

            self.flag_secured_connection_built = True

        else:
            self.send(b"AUTHENTICATION_ONLY\a")

        return ret

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
                time.sleep(0.0001)
            if timeout == 0 or (time.time() - t) > timeout:
                break

        return ret
