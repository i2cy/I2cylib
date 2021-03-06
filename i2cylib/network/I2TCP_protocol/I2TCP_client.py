#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Filename: I2TCP_client
# Created on: 2021/1/10

import socket
import threading
import sys
import time
import uuid
from hashlib import md5


VERSION = "1.1"


class logger: # Logger
    def __init__(self, filename=None, line_end="lf",
                 date_format="%Y-%m-%d %H:%M:%S", level="DEBUG", echo=True):
        self.level = 1
        self.echo = echo
        if level == "DEBUG":
            self.level = 0
        elif level == "INFO":
            self.level = 1
        elif level == "WARNING":
            self.level = 2
        elif level == "ERROR":
            self.level = 3
        elif level == "CRITICAL":
            self.level = 4
        else:
            raise Exception("logger level: DEBUG, INFO, WARNING, ERROR, CRITICAL")
        try:
            temp = time.strftime(date_format)
            del temp
        except Exception as err:
            raise Exception("Failed to set date formant, result: " + str(err))
        self.date_format = date_format
        if line_end == "lf":
            self.line_end = "\n"
        elif line_end == "crlf":
            self.line_end = "\r\n"
        else:
            raise Exception("Unknow line end character(s): \"" + line_end + "\"")
        self.filename = filename
        if filename == None:
            return
        try:
            log_file = open(filename,"w")
            log_file.close()
        except Exception as err:
            raise Exception("Can't open file: \"" + filename + "\", result: " + str(err))
    def DEBUG(self,msg):
        if self.level > 0:
            return
        infos = "["+ time.strftime(self.date_format) +"] [DBUG] " + msg + self.line_end
        if self.echo:
            sys.stdout.write(infos)
            sys.stdout.flush()
        if self.filename == None:
            return
        log_file = open(self.filename,"a")
        log_file.write(infos)
        log_file.close()
        return infos
    def INFO(self,msg):
        if self.level > 1:
            return
        infos = "["+ time.strftime(self.date_format) +"] [INFO] " + msg + self.line_end
        if self.echo:
            sys.stdout.write(infos)
            sys.stdout.flush()
        if self.filename == None:
            return
        log_file = open(self.filename,"a")
        log_file.write(infos)
        log_file.close()
        return infos
    def WARNING(self,msg):
        if self.level > 2:
            return
        infos = "["+ time.strftime(self.date_format) +"] [WARN] " + msg + self.line_end
        if self.echo:
            sys.stdout.write(infos)
            sys.stdout.flush()
        if self.filename == None:
            return
        log_file = open(self.filename,"a")
        log_file.write(infos)
        log_file.close()
        return infos
    def ERROR(self,msg):
        if self.level > 3:
            return
        infos = "["+ time.strftime(self.date_format) +"] [EROR] " + msg + self.line_end
        if self.echo:
            sys.stdout.write(infos)
            sys.stdout.flush()
        if self.filename == None:
            return
        log_file = open(self.filename,"a")
        log_file.write(infos)
        log_file.close()
        return infos
    def CRITICAL(self,msg):
        infos = "["+ time.strftime(self.date_format) +"] [CRIT] " + msg + self.line_end
        if self.echo:
            sys.stdout.write(infos)
            sys.stdout.flush()
        if self.filename == None:
            return
        log_file = open(self.filename,"a")
        log_file.write(infos)
        log_file.close()
        return infos


class dynKey: # 64-Bits dynamic key generator/matcher

    def __init__(self, key, flush_times=1, multiplier=0.01):
        if isinstance(key, str):
            key = key.encode()
        elif isinstance(key, bytes):
            pass
        else:
            raise Exception("private key must be String or Bytes")
        self.key = key
        self.multiplier = multiplier
        if flush_times <= 0:
            flush_times = 1
        self.flush_time = flush_times


    def keygen(self, offset=0): # 64-Bits dynamic key generator
        time_unit = int(time.time() * self.multiplier) + int(offset)
        time_unit = str(time_unit).encode()
        time_unit = md5(time_unit).digest()
        key_unit = md5(self.key).digest()
        sub_key_unit = time_unit + key_unit

        for i in range(self.flush_time):
            sub_key_unit = md5(sub_key_unit).digest()[::-1]
            conv_core = [int((num + 1*self.multiplier) % 255 + 1) for num in sub_key_unit[:3]]
            conv_res = []
            for i2, ele in enumerate(sub_key_unit[3:-2]):
                conv_res_temp = 0
                for c in range(3):
                    conv_res_temp += sub_key_unit[3+i2+c] * conv_core[c]
                conv_res.append(int(conv_res_temp%256))
            sub_key_unit = md5(sub_key_unit[:3] + bytes(conv_core)).digest()[::-1]
            sub_key_unit += md5(sub_key_unit + bytes(conv_res)).digest()
            sub_key_unit += md5(bytes(conv_res)).digest()
            sub_key_unit += md5(bytes(conv_res) + self.key).digest()
            sub_key_unit += key_unit

        conv_cores = [[time_unit[i2] for i2 in range(4*i, 4*i+4)]
                      for i in range(4)]

        for i, ele in enumerate(conv_cores):
            ele.insert(2, 1*self.multiplier + (key_unit[i] + key_unit[i+4] + key_unit[i+8] + key_unit[i+12]) // 4)

        final_key = sub_key_unit

        for i in range(4):
            conv_core = conv_cores[i]
            conv_res = []
            for i2, ele in enumerate(final_key[:-4]):
                conv_res_temp = 0
                for c in range(5):
                    conv_res_temp += final_key[i2+c] * conv_core[c]
                conv_res.append(int(conv_res_temp%256))
            final_key = bytes(conv_res)

        return final_key

    def keymatch(self, key): # Live key matcher
        lock_1 = self.keygen(-1)
        lock_2 = self.keygen(0)
        lock_3 = self.keygen(1)
        lock = [lock_1,lock_2,lock_3]
        if key in lock:
            return True
        else:
            return False


class I2TCPclient:

    def __init__(self, hostname, port=27631, key="basic",
                 watchdog_timeout=15, logger=logger()):
        self.address = (hostname, port)
        self.clt = None
        self.keygen = dynKey(key)
        self.live = False
        self.log_header = "[I2TCP]"
        self.logger = logger
        self.version = VERSION.encode()

        self.mac_id = uuid.UUID(int = uuid.getnode()).bytes[-6:]

        self.watchdog_waitting = 0
        self.watchdog_timeout = watchdog_timeout * 2
        self.threads = {"heartbeat": False,
                        "watchdog": False}
        self.connected = False

    def _packager(self, data):
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
            pak += md5(pak+header_unit).digest()[:3]
            pak += data[offset:length - left]
            offset = length - left
            paks.append(pak)
        return paks

    def _depacker(self, pak_data):
        pak_type = pak_data[0]
        header_unit = self.version + self.keygen.key
        if pak_type == ord("H"):
            ret = None
        elif pak_type == ord("A"):
            ret = {"total_length": int.from_bytes(pak_data[1:4], byteorder='big', signed=False),
                   "package_length": int.from_bytes(pak_data[4:6], byteorder='big', signed=False),
                   "header_md5": pak_data[6:9],
                   "data":pak_data[9:]}
            header_md5 = md5(pak_data[0:6]+header_unit).digest()[:3]
            if header_md5 != ret["header_md5"]:
                ret = None
        else:
            ret = None
        return ret

    def _heartbeat_thread(self):
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
                                b"Heartbeat"
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
            self.logger.ERROR("{} {} heartbeat error, {}".format(self.log_header, local_header, err))

        self.logger.DEBUG("{} {} thread stopped".format(self.log_header, local_header))
        self.threads.update({"heartbeat": False})

    def _watchdog_thread(self):
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
            self.logger.ERROR("{} {} watchdog error, {}".format(self.log_header, local_header, err))

        self.logger.DEBUG("{} {} thread stopped".format(self.log_header, local_header))
        self.threads.update({"watchdog": False})

    def _feed_watchdog(self):
        self.watchdog_waitting = 0

    def _start(self):
        if not self.threads["heartbeat"]:
            heartbeat_thr = threading.Thread(target=self._heartbeat_thread)
            heartbeat_thr.start()
        if not self.threads["watchdog"]:
            watchdog_thr = threading.Thread(target=self._watchdog_thread)
            watchdog_thr.start()

    def reset(self):
        self.live = False
        try:
            self.clt.close()
        except:
            pass
        self.clt = None
        self.connected = False

    def connect(self):
        if self.connected:
            self.logger.ERROR("{} server has already connected".format(self.log_header))
            return self.connected
        clt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clt.settimeout(10)
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

        return self.connected

    def send(self, data):
        if self.clt is None or not self.connected:
            raise Exception("no connection built yet")
        paks = self._packager(data)
        sent = 0
        try:
            for i in paks:
                ret = self.clt.sendall(i)
                sent += len(i)
                self._feed_watchdog()
        except Exception as err:
            self.logger.ERROR("{} failed to send message, {}".format(self.log_header, err))

        return sent

    def recv(self):
        if self.clt is None or not self.connected:
            raise Exception("no connection built yet")

        all_data = None
        try:
            ret = None
            while ret is None:
                pak = self.clt.recv(9)
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
            all_data = data
            while len(all_data) < total_length:
                pak = self.clt.recv(9)
                ret = self._depacker(pak)
                if ret is None:
                    raise Exception("broken package")
                data = b""
                length = 0
                while length != ret["package_length"]:
                    length = len(data)
                    data += self.clt.recv(ret["package_length"] - length)
                all_data += data
        except Exception as err:
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
    clt = I2TCPclient(test_hostname, logger=logger(filename="client_testrun.log"))
    if not clt.connect():
        print("trying to connect to local test server")
        clt.reset()
        clt = I2TCPclient("localhost", logger=logger(filename="client_testrun.log"))
        clt.connect()
    gtc = ""
    for i in range(3):
        pic_data = open("test_pic.png", "rb").read()
        clt.send(pic_data)
        data = clt.recv()
        print("## -test- ## pic test result: {}".format(pic_data == data))
        pic_data = open("I2TCP_server.py", "rb").read()
        clt.send(pic_data)
        data = clt.recv()
        print("## -test- ## file test result: {}".format(pic_data == data))
    pic_data = open("I2TCP_server.py", "rb").read()
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
