#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: I2cylib
# Filename: server
# Created on: 2021/9/29


from i2cylib.network.I2TCP_protocol.I2TCP_server import *
from i2cylib.utils.logger.logger import Logger


class Server(I2TCPserver):

    def __init__(self, key=b"I2TCPbasicKey", port=24678,
                 max_con=20, logger=Logger()):
        """
        modified I2TCP server class

        :param key: str(or bytes), dynamic key for authentication
        :param port: int, server port that to be bond
        :param max_con: int, max TCP connection(s) that allowed
                        to be accept at the same time
        :param logger: Logger, server log output object
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


class Handler(I2TCPhandler):

    def __init__(self, srv, addr, parent, timeout=20,
                 buffer_max=256, watchdog_timeout=15, temp_dir="temp"):
        super(Handler, self).__init__(srv, addr, parent, timeout=20,
                                      buffer_max=256, watchdog_timeout=15, temp_dir="temp")

    def get(self, header=None, timeout=0):
        """
        receive a whole package from client

        :param header: bytes, package header to get the specified package
        :param timeout: int (default: 0), timeout for not
        receiving data from client
        :return: bytes, depacked data
        """

        ret = None
        t = time.time()
        while True:
            if len(self.package_buffer) > 0:
                for i, ele in enumerate(self.package_buffer):
                    if ele[:len(header)] == header or header is None:
                        got = self.package_buffer.pop(i)
                        ret = got
                        break
                break
            if timeout == 0 or (time.time() - t) > timeout:
                break

            time.sleep(0.002)

        return ret
