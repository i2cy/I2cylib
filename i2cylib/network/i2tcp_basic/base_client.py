#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Filename: I2TCP_client
# Created on: 2021/1/10

import socket
import threading
import time
import uuid
import random
from hashlib import md5, sha256
from i2cylib.crypto.keygen import DynKey, DynKey16
from i2cylib.crypto.iccode import Iccode
from i2cylib.utils.logger import Logger

VERSION = "1.5"


class I2TCPclient:

    def __init__(self, hostname, port=27631, key=b"basic",
                 watchdog_timeout=15, logger=None):
        """
        I2TCPclient Class

        :param hostname: str, server address
        :param port: int, server port
        :param key: bytes, dynamic key for authentication
        :param watchdog_timeout: int, watchdog timeout
        :param logger: Logger, client log output object
        """
        self.address = (hostname, port)
        self.clt = None
        self.keygen = DynKey(key)
        self.keygen_preAuth = DynKey16(md5(key).digest())
        self.key = key
        self.live = False
        self.log_header = "[I2TCP]"

        if not isinstance(logger, Logger):
            logger = Logger()

        self.logger = logger
        self.version = VERSION.encode()
        self.busy = False

        self.mac_id = uuid.uuid1().bytes  # 16位客户端UUID

        self.watchdog_waitting = 0
        self.watchdog_timeout = watchdog_timeout * 2
        self.threads = {"heartbeat": False,
                        "watchdog": False}
        self.connected = False

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

    def _depacker(self, pak_data):
        """
        depack packed data to normal data format

        :param pak_data: bytes, packed data
        :return: bytes, data
        """

        header_unit = self.version + self.keygen.key
        pak_type = pak_data[0]

        if pak_type == ord("H"):
            ret = "heartbeat"
        elif pak_type == ord("A"):
            ret = {"total_length": int.from_bytes(pak_data[1:4], byteorder='big', signed=False),
                   "package_length": int.from_bytes(pak_data[4:6], byteorder='big', signed=False),
                   "header_sum": pak_data[6],
                   "payload_sum": pak_data[7:9],
                   "package_id": pak_data[9],
                   "data": pak_data[10:]}
            header_sum = md5(pak_data[0:6] + header_unit).digest()[2]
            if header_sum != ret["header_sum"]:
                ret = None
        else:
            ret = None
        return ret

    def _heartbeat_thread(self):
        """
        watchdog heartbeat service, this keeps connection alive

        :return: None
        """

        self.threads.update({"heartbeat": True})
        local_header = "[heartbeat]"
        self.logger.DEBUG("{} {} thread started".format(self.log_header, local_header))

        try:
            tick = 0
            while self.live:
                if tick >= 4:
                    tick = 0
                    if self.watchdog_waitting > (self.watchdog_timeout // 2):
                        try:
                            self.clt.sendall(
                                b"Heartbeat_"
                            )
                            self.logger.DEBUG("{} {} heartbeat sent".format(self.log_header, local_header))
                            self._feed_watchdog()
                        except Exception as err:
                            self.logger.WARNING("{} {} failed to send heartbeat, {}".format(self.log_header,
                                                                                            local_header,
                                                                                            err))
                time.sleep(0.5)
                tick += 1
        except Exception as err:
            if self.live:
                self.logger.ERROR("{} {} heartbeat error, {}".format(self.log_header, local_header, err))

        self.logger.DEBUG("{} {} thread stopped".format(self.log_header, local_header))
        self.threads.update({"heartbeat": False})

    def _watchdog_thread(self):
        """
        watchdog service, keeps connection available

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
                        self.logger.ERROR("{} {} server seems not responding, disconnecting...".format(self.log_header,
                                                                                                       local_header))
                        self.reset()

                if self.clt is None or not self.connected:
                    self.logger.INFO("{} {} connection lost".format(self.log_header, local_header))
                    self.reset()
                    break

                time.sleep(0.5)
                tick += 1
                self.watchdog_waitting += 1
        except Exception as err:
            if self.live:
                self.logger.ERROR("{} {} watchdog error, {}".format(self.log_header, local_header, err))

        self.logger.DEBUG("{} {} thread stopped".format(self.log_header, local_header))
        self.threads.update({"watchdog": False})

    def _feed_watchdog(self):
        """
        reset the timer of watchdog to keep watchdog from timeout

        :return: None
        """

        self.watchdog_waitting = 0

    def _start(self):
        """
        start watchdog service and heartbeat service

        :return: None
        """

        if not self.threads["heartbeat"]:
            heartbeat_thr = threading.Thread(target=self._heartbeat_thread)
            heartbeat_thr.start()
        if not self.threads["watchdog"]:
            watchdog_thr = threading.Thread(target=self._watchdog_thread)
            watchdog_thr.start()

    def reset(self):
        """
        reset connection status (close the connection)

        :return: None
        """

        self.live = False
        try:
            self.clt.close()
        except:
            pass
        self.clt = None
        self.connected = False

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
            pre_auth_key = self.keygen_preAuth.keygen()
            clt.send(pre_auth_key)
            self.logger.DEBUG("{} pre-auth dynkey sent: {}".format(
                self.log_header, pre_auth_key
            ))

            ts = time.time()
            rand_num = b""
            while len(rand_num) != 64:
                rand_num += clt.recv(64 - len(rand_num))
                if time.time() - ts > timeout:
                    raise Exception("timeout while receiving random data from server")

            self.logger.DEBUG("{} 64-bit random key received: {}".format(
                self.log_header,
                rand_num
            ))

            key_sha256 = sha256()
            key_sha256.update(self.key)
            mix_sha256 = sha256()
            mix_sha256.update(key_sha256.digest() + rand_num)
            mix_coder = Iccode(mix_sha256.digest(), fingerprint_level=6)
            dynamic_key = self.keygen.keygen()
            dynamic_key = mix_coder.encode(dynamic_key)

            clt.sendall(dynamic_key)
            feedback = clt.recv(65536)
            if feedback != self.version:
                raise Exception("invalid key or invalid server, feedback: {}".format(feedback))
            clt.sendall(b"OK")
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

        return self.connected

    def send(self, data):
        """
        send data to connected server

        :param data: bytes
        :return: int, total data length (include headers)
        """

        if self.clt is None or not self.connected:
            raise Exception("no connection built yet")
        paks = self._packager(data)
        sent = 0

        while self.busy:
            time.sleep(0.0001)

        self.busy = True

        try:
            for i in paks:
                ret = self.clt.sendall(i)
                sent += len(i)
                self._feed_watchdog()
        except Exception as err:
            self.logger.ERROR("{} failed to send message, {}".format(self.log_header, err))

        self.busy = False

        return sent

    def recv(self, exception=True):
        """
        receive a package from server

        :return: bytes, depacked data
        """

        if self.clt is None or not self.connected:
            raise Exception("no connection built yet")

        all_data = b""
        try:
            ret = None
            while ret is None:
                pak = b"\x00"
                while pak[0] not in (72, 65):
                    pak = self.clt.recv(1)
                    if pak == b"":
                        return None
                while len(pak) < 10:
                    pak += self.clt.recv(10 - len(pak))
                if pak == b"":
                    self.logger.INFO("{} connection lost".format(self.log_header))
                    self.reset()
                    raise Exception("no connection built yet")
                ret = self._depacker(pak)
            total_length = ret["total_length"]
            self.logger.DEBUG("{} receiving data of total length {}".format(self.log_header, total_length))
            data = b""
            length = 0
            while length != ret["package_length"]:
                length = len(data)
                data += self.clt.recv(ret["package_length"] - length)
            payload_sum = md5(data).digest()[:2]
            if payload_sum != ret["payload_sum"]:
                self.logger.WARNING("{} broken package received".format(self.log_header))
                raise Exception("broken package")
            all_data = data
            while len(all_data) < total_length:
                pak = b"\x00"
                while pak[0] not in (72, 65):
                    pak = self.clt.recv(1)
                    if pak == b"":
                        return None
                while len(pak) < 10:
                    pak += self.clt.recv(10 - len(pak))
                ret = self._depacker(pak)
                if ret is None:
                    raise Exception("broken package")
                data = b""
                length = 0
                while length != ret["package_length"]:
                    length = len(data)
                    data += self.clt.recv(ret["package_length"] - length)
                payload_sum = md5(data).digest()[:2]
                if payload_sum != ret["payload_sum"]:
                    self.logger.WARNING("{} broken package received".format(self.log_header))
                    raise Exception("broken package")
                all_data += data
        except Exception as err:
            if exception and self.live:
                self.logger.ERROR("{} failed to receive message, {}".format(self.log_header, err))
            all_data = None

        return all_data


def init():
    pass


def receive_loop_test(clt):
    while clt.live:
        try:
            data = clt.recv()
            print("## -test- ## data received: {}".format(data))
        except:
            continue
        time.sleep(0.5)


def test():
    test_hostname = "i2cy.tech"
    clt = I2TCPclient(test_hostname, logger=Logger(filename="client_testrun.log"))
    if not clt.connect():
        print("trying to connect to local test server")
        clt.reset()
        clt = I2TCPclient("localhost", key=b"testtest123", logger=Logger(filename="client_testrun.log"))
        clt.connect()
        time.sleep(1)
    if not clt.connect():
        clt.reset()
        clt = I2TCPclient("localhost", key=b"basic", logger=Logger(filename="client_testrun.log"))
        clt.connect()
    gtc = ""
    for i in range(3):
        pic_data = open("test_pic.png", "rb").read()
        clt.send(pic_data)
        data = clt.recv()
        print("## -test- ## pic test result: {}".format(pic_data == data))
        pic_data = open("base_server.py", "rb").read()
        clt.send(pic_data)
        data = clt.recv()
        print("## -test- ## file test result: {}".format(pic_data == data))
    pic_data = open("base_server.py", "rb").read()
    clt.send(pic_data)
    clt.send(pic_data)
    clt.send(pic_data)
    data1 = clt.recv()
    data2 = clt.recv()
    data3 = clt.recv()
    res = pic_data == data1 and pic_data == data2 and pic_data == data3
    print("## -test- ## quick send file test result: {}".format(res))
    listener = threading.Thread(target=receive_loop_test, args=(clt,))
    listener.start()
    while not gtc in ("q", "quit", "exit"):
        try:
            gtc = input("input data to send (q to exit): ")
            clt.send(gtc.encode())
        except KeyboardInterrupt:
            break
    clt.reset()


if __name__ == '__main__':
    init()
    test()
else:
    init()
