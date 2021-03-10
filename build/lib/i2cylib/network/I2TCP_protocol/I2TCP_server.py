#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Filename: I2TCP_server
# Created on: 2021/1/11

import socket
import threading
import time
import sys
import uuid
from hashlib import md5


VERSION = "1.1"


class logger:  # Logger
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
            log_file = open(filename, "w")
            log_file.close()
        except Exception as err:
            raise Exception("Can't open file: \"" + filename + "\", result: " + str(err))

    def DEBUG(self, msg):
        if self.level > 0:
            return
        infos = "[" + time.strftime(self.date_format) + "] [DBUG] " + msg + self.line_end
        if self.echo:
            sys.stdout.write(infos)
            sys.stdout.flush()
        if self.filename == None:
            return
        log_file = open(self.filename, "a")
        log_file.write(infos)
        log_file.close()
        return infos

    def INFO(self, msg):
        if self.level > 1:
            return
        infos = "[" + time.strftime(self.date_format) + "] [INFO] " + msg + self.line_end
        if self.echo:
            sys.stdout.write(infos)
            sys.stdout.flush()
        if self.filename == None:
            return
        log_file = open(self.filename, "a")
        log_file.write(infos)
        log_file.close()
        return infos

    def WARNING(self, msg):
        if self.level > 2:
            return
        infos = "[" + time.strftime(self.date_format) + "] [WARN] " + msg + self.line_end
        if self.echo:
            sys.stdout.write(infos)
            sys.stdout.flush()
        if self.filename == None:
            return
        log_file = open(self.filename, "a")
        log_file.write(infos)
        log_file.close()
        return infos

    def ERROR(self, msg):
        if self.level > 3:
            return
        infos = "[" + time.strftime(self.date_format) + "] [EROR] " + msg + self.line_end
        if self.echo:
            sys.stdout.write(infos)
            sys.stdout.flush()
        if self.filename == None:
            return
        log_file = open(self.filename, "a")
        log_file.write(infos)
        log_file.close()
        return infos

    def CRITICAL(self, msg):
        infos = "[" + time.strftime(self.date_format) + "] [CRIT] " + msg + self.line_end
        if self.echo:
            sys.stdout.write(infos)
            sys.stdout.flush()
        if self.filename == None:
            return
        log_file = open(self.filename, "a")
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


class I2TCPserver:

    def __init__(self, key="basic", port=27631, max_con=20, logger=logger()):
        self.port = port
        self.srv = None
        self.keygen = dynKey(key)
        self.max_con = max_con

        self.logger = logger
        self.log_header = "[I2TCP]"
        self.version = VERSION.encode()

        self.threads = {"watchdog": False,
                        "mainloop": False}
        self.connections = {}

        self.live = False

    def _watchdog_thread(self):
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
            self.logger.ERROR("{} mainloop error, {}".format(self.log_header, local_header, err))

        self.logger.DEBUG("{} {} thread stopped".format(self.log_header, local_header))
        self.threads.update({"mainloop": False})

    def start(self, port=None):
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

    def get_connection(self):
        ret = None
        for i in range(self.max_con):
            if self.connections[i] is None:
                continue
            if not self.connections[i]["handled"]:
                ret = self.connections[i]["handler"]
                self.connections[i]["handled"] = True

        return ret


class I2TCPhandler:

    def __init__(self, srv, addr, parent, timeout=20,
                 buffer_max=256, watchdog_timeout=15, temp_dir="temp"):
        self.addr = addr
        self.srv = srv
        self.keygen = parent.keygen
        self.logger = parent.logger
        self.version = parent.version
        self.live = True

        self.log_header = "[I2TCP] [{}:{}]".format(self.addr[0], self.addr[1])

        self.watchdog_waitting = 0
        self.threads = {"watchdog": False,
                        "receiver": False}
        self.package_buffer = []
        self.srv.settimeout(timeout)

        self.buffer_max = buffer_max
        self.watchdog_timeout = watchdog_timeout * 2
        self.temp_dir = temp_dir
        self.parent = parent

        self.mac_id = uuid.UUID(int=uuid.getnode()).bytes[-6:]

        if self._auth():
            self._start()
        else:
            self.kill()

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
            header_md5 = md5(pak_data[0:6]+header_unit).digest()[:3]
            if header_md5 != ret["header_md5"]:
                ret = None
        else:
            ret = None
        return ret

    def _receiver_thread(self):
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
                    self.package_buffer.append(pak)

        except Exception as err:
            self.logger.ERROR("{} {} error while running, {}".format(self.log_header, local_header, err))

        self.logger.DEBUG("{} {} thread stopped".format(self.log_header, local_header))
        self.threads.update({"receiver": False})

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
                        self.package_buffer = []

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
        self.watchdog_waitting = 0

    def _auth(self):
        self.logger.DEBUG("{} connected".format(self.log_header))
        ret = False

        try:
            dynamic_key = self.srv.recv(65536)
            if self.keygen.keymatch(dynamic_key):
                ret = True
                self.srv.sendall(b"OK")
                self.logger.DEBUG("{} authorized".format(self.log_header))
            else:
                self.logger.WARNING("{} unauthorized connection, key received: {}".format(self.log_header,
                                                                                     dynamic_key))

        except Exception as err:
            self.logger.WARNING("{} authentication process failure, {}".format(self.log_header, err))

        return ret

    def _recv(self):
        all_data = None

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
        if not self.threads["receiver"]:
            thr = threading.Thread(target=self._receiver_thread)
            thr.start()
        if not self.threads["watchdog"]:
            thr = threading.Thread(target=self._watchdog_thread)
            thr.start()

    def kill(self):
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
                self.logger.ERROR("{} failed to kill handler thread(s), timeout")
                break

    def send(self, data):
        packs = self._packager(data)
        sent = 0
        try:
            for i in packs:
                ret = self.srv.sendall(i)
                sent += len(i)
                self._feed_watchdog()
        except Exception as err:
            self.logger.ERROR("{} failed to send data, {}".format(self.log_header, err))

        return sent

    def recv(self):
        ret = None
        if len(self.package_buffer) > 0:
            got = self.package_buffer.pop(0)
            ret = got

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
    srv = I2TCPserver(logger=logger(filename="server_testrun.log"))
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