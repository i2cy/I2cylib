#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: I2cylib
# Filename: i2scan
# Created on: 2021/12/27

import threading
import socket
import time
from i2cylib.utils.stdout.echo import Echo
from i2cylib.utils.time.trf_time import trf_time
from i2cylib.utils.args.get_args import get_args


class I2Target(object):

    def __init__(self, hosts, ports, max_thread_allowed=512, echo=None):
        """
        :param hosts: list(str)
        :param ports: list(int)
        :param max_thread_allowed: int
        :param echo: Echo
        """
        if not isinstance(echo, Echo):
            echo = Echo()
        self.echo = echo

        self.hosts = hosts
        self.ports = ports

        self.max_thread_allowed = max_thread_allowed

        self.flag_scanned = False

        self.thread_running = 0

        self.scan_res = {host: {
            port: {
                "testing": False,
                "is_open": False
            } for port in self.ports
        } for host in self.hosts}

        self.os_res = {host: False for host in self.hosts}

    def __len__(self):
        return len(self.hosts) * len(self.ports)

    def __getitem__(self, item):
        if not self.flag_scanned:
            self.scan()
        return self.scan_res[item]

    def __scan__(self, ip, port, timeout=3, verbose=False, self_update=True):
        pass

    def scan(self, timeout=3, wait=True, verbose=False, msg=b"GET /index.html HTTP/1.1"):
        if wait:
            st = time.time()
            dt = 0
            n = 0
            na = len(self.hosts) * len(self.ports)
            if verbose:
                self.echo.print("________TARGET_________|_STATE_|__PING___|____RESPONSE____")
            for ip in self.hosts:
                for port in self.ports:
                    if verbose and time.time() - dt > 0.25:
                        dt = time.time()
                        self.echo.buttom_print("{}:{:0>2}:{:0>2}  sanning..  ({}/{})    "
                                               "running threads: {}".format(*trf_time(int(time.time() - st)),
                                                                            n, na,
                                                                            self.thread_running))
                    while self.thread_running >= self.max_thread_allowed:
                        if verbose and time.time() - dt > 0.25:
                            dt = time.time()
                            self.echo.buttom_print("{}:{:0>2}:{:0>2}  sanning..  ({}/{})    "
                                                   "running threads: {}".format(*trf_time(int(time.time() - st)),
                                                                                n, na,
                                                                                self.thread_running))
                        time.sleep(0.001)
                    while True:
                        try:
                            threading.Thread(target=self.__scan__, args=(ip, port, timeout, verbose, True, msg)).start()
                            break
                        except:
                            continue
                    n += 1

            n = 0
            while self.thread_running:
                if verbose:
                    if not n:
                        n = 25
                        self.echo.buttom_print("{}:{:0>2}:{:0>2}  waiting..    "
                                               "running threads: {}".format(*trf_time(int(time.time() - st)),
                                                                            self.thread_running))
                    n -= 1
                time.sleep(0.01)
            if verbose:
                self.echo.buttom_print("{}:{:0>2}:{:0>2}  scan completed".format(
                    *trf_time(int(time.time() - st))))
        else:
            threading.Thread(target=self.scan, args=(timeout, True, verbose, msg)).start()

        self.flag_scanned = True

        return self

    def is_open(self, host, port):
        """
        return the target port status, return None if it is still in testing

        :param host: str
        :param port: int
        :return: bool or None
        """
        ret = None
        if not self.flag_scanned:
            self.scan()
        if not self[host][port]["testing"]:
            ret = self[host][port]["is_open"]
        return ret


class FullScan(I2Target):

    def __init__(self, hosts, ports, max_thread_allowed=512, echo=None):
        """
        :param hosts: list(str)
        :param ports: list(int)
        """
        super(FullScan, self).__init__(hosts, ports, max_thread_allowed=max_thread_allowed, echo=echo)

        self.scan_res = {host: {
            port: {
                "testing": False,
                "is_open": False,
                "feedback": b""
            } for port in self.ports
        } for host in self.hosts}

    def __scan__(self, ip, port,
                 timeout=3,
                 verbose=False,
                 update_self=True,
                 msg=b"GET /index.html HTTP/1.1"):
        self.thread_running += 1
        # print("thread scan started port {}".format(port))
        if update_self:
            self.scan_res[ip][port]["testing"] = True
            self.scan_res[ip][port]["is_open"] = False

        clt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clt.settimeout(timeout)
        try:
            ts = time.time()
            clt.connect((ip, port))
            ta = time.time() - ts
            ret = b"(err) connected successfully"
            if update_self:
                self.scan_res[ip][port]["is_open"] = True
        except Exception as err:
            ret = b"(err) failed to build connection"
        try:
            original_feedback = self.scan_res[ip][port]["feedback"]
            if msg:
                clt.sendall(msg)
                ret = clt.recv(2048)
            if not update_self:
                self.scan_res[ip][port]["feedback"] = original_feedback
            clt.close()
        except Exception as err:
            # raise err
            pass

        if self.scan_res[ip][port]["is_open"] and verbose:
            open = "OPEN "
            self.echo.print("{:>16}:{:<5} | {} | {: >4} ms | {}".format(ip, port, open, int(ta * 1000), ret))

        self.thread_running -= 1
        if update_self:
            self.scan_res[ip][port]["testing"] = False
        # print("thread scan closed port {}".format(port))
        return ret

    def get_feedback(self, host, port):
        """
        return the target port feedback, return None if it is still in testing

        :param host: str
        :param port: int
        :return: bool or None
        """
        ret = None
        if not self.flag_scanned:
            self.scan()
        if not self[host][port]["testing"]:
            ret = self[host][port]["feedback"]
        return ret


def mannual(echo=None):
    if not isinstance(echo, Echo):
        echo = Echo()
    echo.print("""Simple TCP Port Scanner [by I2cy] v1.0

Usage: i2scan <-t TARGET_ADDRESSES> [-p PORTS] [-m MSG] 
              [-mt MAX_THREADS_NUM] [-to TIMEOUT_SECOND]

Options:
 -t --target TARGET_ADDRESSES   - set the target hostname format with
                                  "address, address", "*" can be used
                                  in IP represent, e.g. "192.168.0.*"
                                  stands for "192.168.0.1~255"

 -p --port TARGET_PORTS         - set target ports to scan in each
                                  address, format with 
                                  "port, port~port" (default: "*")
                                  "*" stands for 1~65535

 -m --msg UTF8_STRING           - set the message to knock on target 
                                  server (default: "GET /index.html 
                                  HTTP/1.1")

 -mt --max-threads INT          - set threads number that running at
                                  the same time (default: 4000),
                                  higher value means faster scan
                                  speed, set to lower value if the 
                                  test result seems to be incorrect

 -to --timeout                  - set the timeout value for each
                                  scanner connection (default: 3),
                                  lower value may result in faster 
                                  scanning speed

 -h --help                      - display this message

Examples:
 >i2scan -t 192.168.31.* -p 22 -to 1
 >i2scan -t "192.168.31.110, 192.168.31.112" -p "22, 2000~50000"
 >i2scan -t 192.168.31.24 -mt 10000 -m "TEST123"
""")


def main():
    echo = Echo()
    opts = get_args()

    hosts = []
    ports = []
    max_threads = 4000
    msg = b"GET /index.html HTTP/1.1"
    timeout = 3

    if opts == {}:
        mannual(echo)
        return -1

    for opt in opts.keys():

        if opt in ("-t", "--target"):
            try:
                targets_raw = opts[opt]
                targets_raw = targets_raw.replace(" ", "")
                targets_raw = targets_raw.split(",")
                for i in targets_raw:
                    target_raw = [i]
                    wait = True
                    while wait:
                        wait = False
                        target_temp = []
                        for i2 in target_raw:
                            if "*" in i2:
                                wait = True
                                ip_raw = i2.split(".")
                                dot_index = ip_raw.index("*")
                                ip_temp = [ip_raw] * 255
                                for i3, ele in enumerate(ip_temp):
                                    ip_temp[i3][dot_index] = str(i3 + 1)
                                    target_temp.append(".".join(ip_temp[i3]))
                            else:
                                target_temp.append(i2)

                        target_raw = target_temp.copy()
                    hosts.extend(target_raw)
            except Exception as err:
                echo.print("error: can not understand the target expression, {}".format(err))
                return -1

        elif opt in ("-p", "--port"):
            try:
                port_raw = opts[opt]
                port_raw = port_raw.replace(" ", "")
                port_raw = port_raw.split(",")
                if "*" in port_raw:
                    ports = []
                else:
                    for i in port_raw:
                        p_raw = i
                        if "~" in p_raw:
                            p_range = p_raw.split("~")
                            p_raw = list(range(int(p_range[0]), int(p_range[1]) + 1))
                        else:
                            p_raw = [int(i)]
                        ports.extend(p_raw)
                if max(ports) > 65535:
                    raise Exception("port must be smaller than 65535")
                elif min(ports) < 1:
                    raise Exception("port must be greater than 1")
            except Exception as err:
                echo.print("error: can not understand the port expression, {}".format(err))
                return -1

        elif opt in ("-m", "--msg", "--message"):
            try:
                msg = opts[opt].encode("utf-8")
            except Exception as err:
                echo.print("error: failed to encode sending message, {}".format(err))
                return -1

        elif opt in ("-mt", "--max-threads"):
            try:
                max_threads = int(opts[opt])
            except Exception as err:
                echo.print("error: max threads number value must be int, {}".format(err))
                return -1

        elif opt in ("-to", "--timeout"):
            try:
                timeout = int(opts[opt])
            except Exception as err:
                echo.print("error: timeout value must be int, {}".format(err))
                return -1

        else:
            mannual(echo)
            return -1

    if not ports:
        ports = list(range(1, 65536))

    try:
        scanner = FullScan(hosts, ports, max_thread_allowed=max_threads, echo=echo)
        try:
            scanner.scan(timeout=timeout, msg=msg, wait=True, verbose=True)
        except KeyboardInterrupt:
            echo.buttom_print("scanner process aborted by keyboard")
    except Exception as err:
        echo.print("error: {}".format(err))
        return -1


def test():
    h = ["i2cy.tech",
         "52.175.59.84",
         "godaftwithebk.pub",
         "an.godaftwithebk.pub"]
    p = list(range(1, 65535))

    t = FullScan(h, p, 4000)
    t.scan(timeout=6, wait=False)
    time.sleep(3)
    print("22:", t['i2cy.tech'][22])
    print("22:", t['i2cy.tech'][22])


if __name__ == '__main__':
    test()
    try:
        main()
    except KeyboardInterrupt:
        exit(-1)
    print("")
