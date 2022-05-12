#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Filename: I2TCP_server
# Created on: 2021/1/11

import socket
import threading
import time
import uuid
from hashlib import md5, sha256
from i2cylib.crypto.keygen import DynKey
from i2cylib.crypto.iccode import Iccode
from i2cylib.utils.logger import Logger
from i2cylib.utils.bytes import random_keygen

VERSION = "1.3"


class I2TCPserver:

    def __init__(self, key=b"basic", port=27631, max_con=20, logger=None):
        """
        I2TCP server class

        :param key: bytes, dynamic key for authentication
        :param port: int, server port that to be bond
        :param max_con: int, max TCP connection(s) that allowed
                        to be accept at the same time
        :param logger: Logger, server log output object
        """

        self.port = port
        self.srv = None
        self.keygen = DynKey(key)
        self.key = key
        self.max_con = max_con

        if not isinstance(logger, Logger):
            logger = Logger()

        self.logger = logger
        self.log_header = "[I2TCP]"
        self.version = VERSION.encode()

        self.threads = {"watchdog": False,
                        "mainloop": False}
        self.connections = {}

        self.live = False

    def _watchdog_thread(self):
        """
        watchdog service, kills connection during server
         shutting down, and removes dead connection in
         buffer

        :return: None
        """

        self.threads.update({"watchdog": True})
        local_header = "[watchdog]"
        self.logger.DEBUG("{} {} thread started".format(self.log_header, local_header))

        try:
            while self.live:
                for i in range(self.max_con):
                    if self.connections[i] is None:
                        continue
                    if not self.connections[i]["handler"].live:
                        self.connections.update({i: None})
                time.sleep(0.5)
            self.logger.DEBUG("{} {} kill signal received".format(self.log_header, local_header))
            self.logger.DEBUG("{} {} waiting for all connection(s) to be killed".format(self.log_header,
                                                                                        local_header))
            tick = 0
            while True:
                alive_con = 0
                for i in range(self.max_con):
                    if self.connections[i] is None:
                        continue
                    if self.connections[i]["handler"].live:
                        alive_con += 1
                if alive_con == 0:
                    self.logger.INFO("{} {} all connection(s) have been killed".format(self.log_header,
                                                                                       local_header))
                    break
                if tick > 30:
                    self.logger.WARNING("{} {} some connection can not be killed".format(self.log_header,
                                                                                         local_header))
                    break
                time.sleep(0.5)
                tick += 1
            self.logger.DEBUG("{} {} killing mainloop".format(self.log_header, local_header))
            try:
                con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                con.connect(("localhost", self.port))
                con.close()
                self.srv.close()
            except Exception as err:
                self.logger.WARNING("{} {} failed to kill mainloop or it has been killed".format(self.log_header,
                                                                                                 local_header))
            self.srv = None

        except Exception as err:
            self.logger.ERROR("{} watchdog error, {}".format(self.log_header, local_header, err))

        self.logger.DEBUG("{} {} thread stopped".format(self.log_header, local_header))
        self.threads.update({"watchdog": False})

    def _mainloop_thread(self):
        """
        server mainloop, accept incoming connection

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
                    handler = I2TCPhandler(con, addr, self)
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
        start I2TCP server

        :param port: int (default self.port), port to be bond
        :return: None
        """

        if port is None:
            port = self.port
        else:
            self.port = port

        try:
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.bind(("0.0.0.0", port))
            srv.listen(self.max_con - 1)
            self.srv = srv

            for i in range(self.max_con):
                self.connections.update({i: None})

            self.live = True

            thr = threading.Thread(target=self._mainloop_thread)
            thr.start()

            thr = threading.Thread(target=self._watchdog_thread)
            thr.start()

            self.logger.INFO("{} server started at 0.0.0.0:{}".format(self.log_header, self.port))

        except Exception as err:
            self.logger.ERROR("{} failed to start server, {}".format(self.log_header, err))

    def kill(self):
        """
        stop the server

        :return: None
        """

        self.live = False
        tick = 0
        alive = True
        while alive:
            alive = False
            live_threads = []
            for i in self.threads.keys():
                if self.threads[i]:
                    live_threads.append(i)
                    alive = True

            if not alive:
                self.logger.INFO("{} server killed".format(self.log_header))

            if tick > 60:
                self.logger.ERROR("{} shutdown timeout, live thread(s): {}".format(self.log_header,
                                                                                   live_threads))
                break
            time.sleep(0.5)
            tick += 1

    def get_connection(self, wait=False):
        """
        get the latest connected connection that yet to be
        handled

        :return: I2TCPhandler, connection handler
        """

        ret = None
        while ret is None and self.live:
            for i in range(self.max_con):
                if self.connections[i] is None:
                    continue
                if not self.connections[i]["handled"]:
                    ret = self.connections[i]["handler"]
                    self.connections[i]["handled"] = True
                    break
            if not wait:
                break

        return ret


class I2TCPhandler:

    def __init__(self, srv, addr, parent, timeout=20,
                 buffer_max=256, watchdog_timeout=15, temp_dir="temp"):
        """
        I2TCP connection handler

        :param srv: socket.socket, socket server object
        :param addr: str, incoming connection address
        :param parent: I2TCPserver, father object
        :param timeout (default: 20): int, timeout for connection
        :param buffer_max (default: 256): int,
        :param watchdog_timeout (default 15):
        :param temp_dir (default: "temp"): cache directory, reserved option
        """

        self.addr = addr
        self.srv = srv
        self.keygen = parent.keygen
        self.logger = parent.logger
        self.version = parent.version
        self.live = True
        self.busy = False

        self.log_header = "[I2TCP] [{}:{}]".format(self.addr[0], self.addr[1])

        self.watchdog_waitting = 0
        self.threads = {"watchdog": False,
                        "receiver": False}
        self.package_buffer = []
        self.srv.settimeout(timeout)

        self.buffer_max = buffer_max
        self.watchdog_timeout = watchdog_timeout * 2
        self.temp_dir = temp_dir

        assert isinstance(parent, I2TCPserver)
        self.parent = parent

        self.mac_id = uuid.UUID(int=uuid.getnode()).bytes[-6:]

        if self._auth():
            self._start()
        else:
            self.kill()

    def _packager(self, data):
        """
        pack data with I2TCP format

        :param data: bytes
        :return: List(bytes), packed data
        """

        offset = 0
        paks = []
        length = len(data)
        left = length
        header_unit = self.version + self.keygen.key
        while left > 0:
            pak = b"A" + left.to_bytes(length=3, byteorder='big', signed=False)
            if left < 60000:
                left = 0
            else:
                left -= 60000
            pak_length = length - left - offset
            pak += pak_length.to_bytes(length=2, byteorder='big', signed=False)
            pak += md5(pak + header_unit).digest()[:3]
            pak += data[offset:length - left]
            offset = length - left
            paks.append(pak)
        return paks

    def _depacker(self, pak_data):
        """
        depack packed data to normal data format

        :param pak_data: bytes, packed data
        :return: bytes, data
        """

        header_unit = self.version + self.keygen.key
        pak_type = pak_data[0]
        ret = None
        if pak_type == ord("H"):
            ret = "heartbeat"
        elif pak_type == ord("A"):
            ret = {"total_length": int.from_bytes(pak_data[1:4], byteorder='big', signed=False),
                   "package_length": int.from_bytes(pak_data[4:6], byteorder='big', signed=False),
                   "header_md5": pak_data[6:9],
                   "data": pak_data[9:]}
            header_md5 = md5(pak_data[0:6] + header_unit).digest()[:3]
            if header_md5 != ret["header_md5"]:
                ret = None
        else:
            ret = None
        return ret

    def _receiver_thread(self):
        """
        data receiving service, receive I2TCP package from client
        and move it to buffer with depacked data

        :return: None
        """

        self.threads.update({"receiver": True})
        local_header = "[receiver]"
        self.logger.DEBUG("{} {} thread started".format(self.log_header, local_header))

        try:
            while self.live:
                try:
                    pak = self._recv()
                except Exception as err:
                    if not self.live:
                        break
                    self.logger.ERROR("{} {} failed to receive data from client, {}".format(self.log_header,
                                                                                            local_header,
                                                                                            err))
                    continue

                if pak is None:
                    self.logger.INFO("{} {} connection lost".format(self.log_header, local_header))
                    threading.Thread(target=self.kill).start()
                else:
                    self.logger.DEBUG("{} {} new package received, buffer size now {}".format(
                        self.log_header,
                        local_header,
                        len(self.package_buffer)))
                    self.package_buffer.append(pak)

        except Exception as err:
            if self.live:
                self.logger.ERROR("{} {} error while running, {}".format(self.log_header, local_header, err))

        self.logger.DEBUG("{} {} thread stopped".format(self.log_header, local_header))
        self.threads.update({"receiver": False})

    def _watchdog_thread(self):
        """
        handler watchdog, keeps connection alive and kills it when
        client is not responding, handle package buffer overflow
        event

        :return: None
        """

        self.threads.update({"watchdog": True})
        local_header = "[watchdog]"
        self.logger.DEBUG("{} {} thread started".format(self.log_header, local_header))

        try:
            tick = 0
            while self.live:
                if tick >= 4:
                    tick = 0
                    if self.watchdog_waitting > self.watchdog_timeout:
                        self.logger.ERROR("{} {} client seems not responding, disconnecting...".format(self.log_header,
                                                                                                       local_header))
                        threading.Thread(target=self.kill).start()
                        break
                if tick % 2 == 0:
                    err = False
                    for i in self.threads.keys():
                        if not self.threads[i]:
                            self.logger.WARNING("{} {} thread \"{}\" seems offline".format(self.log_header,
                                                                                           local_header,
                                                                                           i))
                            err = True
                    if err:
                        self._start()

                    if len(self.package_buffer) > self.buffer_max:
                        self.logger.ERROR("{} {} package buffer overflowed, cleaning...".format(self.log_header,
                                                                                                local_header))
                        while len(self.package_buffer) > self.buffer_max:
                            self.package_buffer.pop(0)

                if not self.parent.live:
                    self.logger.DEBUG("{} {} parent loop stopping, killing handler".format(self.log_header,
                                                                                           local_header))
                    threading.Thread(target=self.kill).start()
                    break

                time.sleep(0.5)
                self.watchdog_waitting += 1
                tick += 1
        except Exception as err:
            self.logger.ERROR("{} {} watchdog error, {}".format(self.log_header, local_header, err))

        self.logger.DEBUG("{} {} thread stopped".format(self.log_header, local_header))
        self.threads.update({"watchdog": False})

    def _feed_watchdog(self):
        """
        reset the timer of watchdog to keep watchdog from timeout

        :return: None
        """

        self.watchdog_waitting = 0

    def _auth(self):
        """
        authentication sequence for incoming connection

        :return: bool, authentication status
        """

        self.logger.DEBUG("{} connected".format(self.log_header))
        ret = False

        try:
            rand_num = random_keygen(64)
            self.srv.sendall(rand_num)

            key_sha256 = sha256()
            key_sha256.update(self.parent.key)
            mix_sha256 = sha256()
            mix_sha256.update(key_sha256.digest() + rand_num)
            mix_coder = Iccode(mix_sha256.digest(), fingerprint_level=6)

            dynamic_key = self.srv.recv(65536)
            dynamic_key = mix_coder.decode(dynamic_key)

            if self.keygen.keymatch(dynamic_key):
                ret = True
                self.srv.sendall(self.version)
                self.logger.DEBUG("{} authorized".format(self.log_header))
            else:
                self.logger.WARNING("{} unauthorized connection, key received: {}".format(self.log_header,
                                                                                          dynamic_key))
            feedback = self.srv.recv(2)
            if feedback != b"OK":
                raise Exception("invalid feedback, {}".format(feedback))

        except Exception as err:
            self.logger.WARNING("{} authentication process failure, {}".format(self.log_header, err))

        return ret

    def _recv(self):
        """
        receive raw data from client socket connection and
        depack it till a whole package is received

        :return: bytes, depacked data
        """

        ret = None
        while ret is None:
            pak = self.srv.recv(9)
            self.logger.DEBUG("{} received package head: {}".format(self.log_header, pak))
            if pak == b"":
                return None
            ret = self._depacker(pak)
            if ret is None:
                self.logger.WARNING("{} broken package received".format(self.log_header))
            if ret == "heartbeat":
                self.logger.DEBUG("{} heartbeat received".format(self.log_header))
                self._feed_watchdog()
                ret = None

        total_length = ret["total_length"]
        self.logger.DEBUG("{} receiving data of total length {}".format(self.log_header,
                                                                        total_length))

        data = b""
        length = 0
        while length != ret["package_length"]:
            length = len(data)
            data += self.srv.recv(ret["package_length"] - length)
        all_data = data
        while len(all_data) < total_length:
            pak = self.srv.recv(9)
            ret = self._depacker(pak)
            if ret is None:
                raise Exception("broken package")
            if ret == "heartbeat":
                self.logger.DEBUG("{} heartbeat received".format(self.log_header))
                self._feed_watchdog()
            data = b""
            length = 0
            while length != ret["package_length"]:
                length = len(data)
                data += self.srv.recv(ret["package_length"] - length)
            all_data += data

        self._feed_watchdog()
        return all_data

    def _start(self):
        """
        start watchdog service and receiver service

        :return: None
        """

        if not self.threads["receiver"]:
            thr = threading.Thread(target=self._receiver_thread)
            thr.start()
        if not self.threads["watchdog"]:
            thr = threading.Thread(target=self._watchdog_thread)
            thr.start()

    def kill(self):
        """
        kill this connection

        :return: None
        """

        self.live = False
        try:
            self.srv.close()
        except:
            pass
        tick = 0
        alive = True
        while alive:
            alive = False
            for i in self.threads.keys():
                if self.threads[i]:
                    alive = True
            time.sleep(0.5)
            tick += 1
            if tick > 30:
                self.logger.ERROR("{} failed to kill handler thread(s), timeout".format(self.log_header))
                break

    def send(self, data):
        """
        send data with I2TCP format to client

        :param data: bytes, regular data
        :return: int, total package length (include header)
        """

        packs = self._packager(data)
        sent = 0

        while self.busy:
            time.sleep(0.0001)

        self.busy = True

        try:
            for i in packs:
                ret = self.srv.sendall(i)
                sent += len(i)
                self._feed_watchdog()
        except Exception as err:
            if self.live:
                self.logger.ERROR("{} failed to send data, {}".format(self.log_header, err))

        self.busy = False

        return sent

    def recv(self, timeout=0):
        """
        receive a whole package from client

        :param timeout: int (default: 0), timeout for not
        receiving data from client
        :return: bytes, depacked data
        """

        ret = None
        t = time.time()
        while ret is None:
            if len(self.package_buffer) > 0:
                got = self.package_buffer.pop(0)
                ret = got
                break

            if timeout:
                time.sleep(0.002)
            elif timeout == 0 or (time.time() - t) > timeout:
                break

        return ret


def init():
    pass


def handler_test(con):
    tick = 0
    while con.live:
        data = con.recv()
        if not data is None:
            tick = 0
            if len(data) > 100:
                data_r = data[:100]
            else:
                data_r = data
            print("## -test- ## data received, length {}: {}".format(len(data), data_r))
            con.send(data)
        if tick > 15:
            tick = 0
            con.send(b"test server heartbeat")
            print("## -test- ## heartbeat sent")
        time.sleep(0.5)
        tick += 1


def test():
    srv = I2TCPserver(logger=Logger(filename="server_testrun.log"))
    srv.start()
    print("(Ctrl+C to exit)")
    try:
        while True:
            con = srv.get_connection()
            if not con is None:
                print("## -test- ## new connection handled")
                threading.Thread(target=handler_test, args=(con,)).start()
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("stopping server")
        srv.kill()


if __name__ == '__main__':
    init()
    test()
else:
    init()
