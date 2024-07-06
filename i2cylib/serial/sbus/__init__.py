#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: I2cylib
# Filename: __init__.py
# Created on: 2024/4/23

import queue
import warnings
from ctypes import c_bool
from multiprocessing import Process, Queue, Value
import threading
import serial
import time

SBUS_NUM_CHANNELS = 16
SBUS_SIGNAL_OK = 0
SBUS_SIGNAL_LOST = 1
SBUS_SIGNAL_FAILSAFE = 2

SBUS_TX_DURATION_SEC = 0.0065


def sbus_decode(frame: bytes):
    """
    decode sbus frame
    :param frame: 25 bytes of sbus frame
    :return: code, list_of_channels[]
    """
    res = []
    payload = int.from_bytes(frame[1:23], byteorder="little")
    for ch in range(0, 16):
        res.append(payload & 0x7ff)
        payload >>= 11

    flag_code = 0
    if frame[-2] & 0b00000100:
        flag_code = SBUS_SIGNAL_LOST
    if frame[-2] & 0b00001000:
        flag_code = SBUS_SIGNAL_FAILSAFE

    return flag_code, res


def sbus_encode(flag_code: int, channels: list):
    """
    encode sbus frame
    :param flag_code: flag code
    :param channels: list of 16 channels
    :return: 25_bytes_of_sbus_frame
    """
    res = b"\x0f"
    payload = 0
    for ch in channels[:0:-1]:
        payload |= ch
        payload <<= 11
    payload |= channels[0]

    res += payload.to_bytes(22, byteorder="little")

    if flag_code == SBUS_SIGNAL_FAILSAFE:
        res += b"\x08\x00"
    elif flag_code == SBUS_SIGNAL_LOST:
        res += b"\x04\x00"
    else:
        res += b"\x00\x00"

    return res


class SBUS:

    def __init__(self, com: str = "/dev/ttyACM0", multiprocess: bool = True, rx: bool = True, tx: bool = False):
        """
        SBUS sender/receiver
        """

        self.com = com
        self.multiprocess_enabled = multiprocess

        self.channels = [1000 for i in range(SBUS_NUM_CHANNELS)]

        self.flag = SBUS_SIGNAL_LOST

        self.__processes = []
        self.__threads = []

        self.__tx = Value(c_bool, tx)
        self.__rx = Value(c_bool, rx)

        self.running = Value(c_bool, False)

        self.__mp_rx = Queue(750)
        self.__mp_tx = Queue(750)

        self.__callback_funcs = []

    def get_channels(self):
        """
        return channel data of SBUS
        :return: list_of_16_channels
        """
        return self.channels

    def get_flag(self):
        """
        return flag value of SBUS, could be: SBUS_SIGNAL_OK = 0, SBUS_SIGNAL_LOST = 1, SBUS_SIGNAL_FAILSAFE = 2
        :return: int
        """
        return self.flag

    def update_channels_and_flag(self, channels: list, flag: int):
        """
        update channels and flag of SBUS only if TX is on
        :param channels: list of 16 channels, starts from ch1
        :param flag: flag of status, could be: SBUS_SIGNAL_OK = 0, SBUS_SIGNAL_LOST = 1, SBUS_SIGNAL_FAILSAFE = 2
        :return:
        """
        if not self.__tx:
            raise Exception("TX is not enabled on this SBUS handler")

        self.channels = channels
        self.flag = flag

        if self.multiprocess_enabled:
            self.__mp_tx.put([flag] + channels)

    def register_callback(self, callback_func: callable):
        """
        register callback function that will be called when SBUS receives/transmits data
        passing arguments: int_flag_value, list_of_16_channels
        :param callback_func: callable function
        :return:
        """
        self.__callback_funcs.append(callback_func)

    def remove_callback(self, callback_func: callable):
        """
        remove callback function that will be called when SBUS receives/transmits data
        :param callback_func:
        :return:
        """
        self.__callback_funcs.remove(callback_func)

    def start(self):
        """
        start SBUS manager
        :return:
        """
        if self.running.value:
            raise Exception("SBUS manager already running")

        self.running.value = True

        if self.multiprocess_enabled:
            # multiprocessing
            self.__processes.append(Process(target=self.__proc_handler, daemon=True))
            self.__threads.append(threading.Thread(target=self.__thread_mp_update))

        else:
            # multithreading
            self.__threads.append(threading.Thread(target=self.__thread_handler))

        [ele.start() for ele in self.__threads]
        [ele.start() for ele in self.__processes]

    def kill(self):
        """
        kill all threads and all processes, stop SBUS manager
        :return:
        """
        self.running.value = False
        [ele.join() for ele in self.__processes]
        [ele.join() for ele in self.__threads]

    # -*- multiprocessing -*-
    def __proc_handler(self):
        """
        Receive sbus frames and put into multiprocessing queue
        :return:
        """
        dev = serial.Serial(port=self.com, baudrate=100000, parity=serial.PARITY_EVEN,
                            stopbits=serial.STOPBITS_TWO,
                            bytesize=serial.EIGHTBITS,
                            timeout=0.004)

        # initialize local buffer for channel data and flag data
        tx_channels = [1000 for i in range(SBUS_NUM_CHANNELS)]
        code = 0

        # local rx task
        def rx(device):
            # RX
            frame = device.read(1)  # read 1 byte of header
            if frame != b"\x0f":  # sync with data frame head
                return

            frame += device.read(24)
            if frame[-1] != 0 or len(frame) != 25:  # skip broken packages
                return

            try:
                self.__mp_rx.put(frame)
            except queue.Full:
                return

        # local tx task
        def tx(device, flag_code, channels):
            # TX
            payload = sbus_encode(flag_code, channels)
            device.write(payload)

        # initialize t0 for TX update frequency control
        t0 = time.time()

        # local kernel
        while self.running.value:

            if self.__rx.value:
                # RX
                rx(dev)

            if self.__tx.value:
                # TX
                t1 = time.time()
                if t1 - t0 >= SBUS_TX_DURATION_SEC:
                    t0 = t1
                    # wait for exact 8.5 ms
                    try:
                        buff = self.__mp_tx.get(block=False)
                        code = buff[0]
                        tx_channels = buff[1:]
                    except queue.Empty:
                        pass
                    tx(dev, code, tx_channels)
                else:
                    time.sleep(0.0001)

    def __thread_mp_update(self):
        """
        update channels through multiprocessing queue
        :return:
        """
        while self.running.value:
            try:
                # update changes from multiprocessing queue to class storage
                self.flag, self.channels = sbus_decode(self.__mp_rx.get(timeout=0.5))
                # callbacks
                for func in self.__callback_funcs:
                    try:
                        func(self.channels, self.flag)
                    except Exception as e:
                        warnings.warn("i2cylib.serial.sbus callback function failed when running, {}".format(e))
            except queue.Empty:
                continue

    # -*- multithreading -*-
    def __thread_handler(self):
        """
        multithreading sbus receiver and processor
        """
        dev = serial.Serial(port=self.com, baudrate=100000, parity=serial.PARITY_EVEN,
                            stopbits=serial.STOPBITS_TWO,
                            bytesize=serial.EIGHTBITS,
                            timeout=0.004)

        # local rx task
        def rx(device):
            # RX
            frame = device.read(1)  # read 1 byte of header
            if frame != b"\x0f":  # sync with data frame head
                return

            frame += device.read(24)  # read the rest of 24 bytes of one frame
            if frame[-1] != 0 or len(frame) != 25:  # skip broken packages
                return

            # print("RX:", frame)

            self.flag, self.channels = sbus_decode(frame)  # update changes

        t0 = time.time()
        # local kernel
        while self.running.value:

            if self.__rx.value:
                rx(dev)

            # callbacks
            for func in self.__callback_funcs:
                try:
                    func(self.channels, self.flag)
                except Exception as e:
                    warnings.warn("i2cylib.serial.sbus callback function failed when running, {}".format(e))

            if self.__tx.value:
                # TX
                t1 = time.time()
                if t1 - t0 >= SBUS_TX_DURATION_SEC:
                    t0 = t1
                    # wait for exact 8.5 ms
                    payload = sbus_encode(self.flag, self.channels)  # encode payload
                    dev.write(payload)  # write to device
                    # print("TX:", payload)
                else:
                    time.sleep(0.0001)


if __name__ == '__main__':
    # print("test on mode multiprocessing, RX only")
    # sbus = SBUS("/dev/ttyACM0", multiprocess=True, rx=True, tx=False)
    # sbus.start()
    # for i in range(10):
    #     print("sbus data: {}, flag: {}".format(sbus.get_channels(), sbus.get_flag()))
    #     time.sleep(0.5)
    # sbus.kill()
    # print("stopped")
    #
    # print("test on mode multithreading, RX only")
    # sbus = SBUS("/dev/ttyACM0", multiprocess=False, rx=True, tx=False)
    # sbus.start()
    # for i in range(10):
    #     print("sbus data: {}, flag: {}".format(sbus.get_channels(), sbus.get_flag()))
    #     time.sleep(0.5)
    # sbus.kill()
    # print("stopped")

    print("test on mode multithreading, proxying RX to TX")
    sbus_rx = SBUS("/dev/ttyACM0", multiprocess=False, rx=True, tx=False)
    sbus_tx = SBUS("/dev/ttyACM1", multiprocess=False, rx=False, tx=True)
    sbus_rx.register_callback(sbus_tx.update_channels_and_flag)
    sbus_rx.start()
    sbus_tx.start()
    for i in range(10):
        rx = (sbus_rx.get_channels(), sbus_rx.get_flag())
        print("sbus data: {}, flag: {}".format(*rx))
        time.sleep(0.5)
    input("press ENTER to stop")
    sbus_tx.kill()
    sbus_rx.kill()
    print("stopped")

    print("test on mode multiprocess, proxying RX to TX\n")
    sbus_rx = SBUS("/dev/ttyACM0", multiprocess=True, rx=True, tx=False)
    sbus_tx = SBUS("/dev/ttyACM1", multiprocess=True, rx=False, tx=True)
    sbus_rx.register_callback(sbus_tx.update_channels_and_flag)
    sbus_rx.start()
    sbus_tx.start()
    try:
        while True:
            rx = (sbus_rx.get_channels(), sbus_rx.get_flag())
            print("\rsbus data: {}, flag: {}             ".format(*rx), end="")
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    sbus_tx.kill()
    sbus_rx.kill()
    print("stopped")
