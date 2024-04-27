#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: I2cylib
# Filename: anotc
# Created on: 2024/4/27

import threading
from typing import Tuple
from i2cylib.hid.utils import find_device
import hid
import struct

VENDOR_ID = 0x0483
PRODUCT_ID = 0xa022


class AnoOpticalFlowSensor(hid.device):

    def __init__(self, custom_addr=0xff, vendor_id=VENDOR_ID, product_id=PRODUCT_ID, wait_for_hotplug=True):
        """
        AnoTC Optical Flow Sensor interface based on hidapi
        :param custom_addr: address set by ano ofs
        :type custom_addr: int
        :param vendor_id: the vendor id of the device, by default VENDOR_ID = 0x0483
        :type vendor_id: int
        :param product_id: the product id of the device, by default PRODUCT_ID = 0xa022
        :type product_id: int
        :param wait_for_hotplug: boolean to wait for hotplug on device
        :type wait_for_hotplug: bool
        """
        super(AnoOpticalFlowSensor, self).__init__()

        self.running = False
        self.addr = custom_addr

        class OfsData:
            dx_raw = 0.0
            dy_raw = 0.0
            quality_raw = 0
            dx_decoupled = 0.0
            dy_decoupled = 0.0
            quality_decoupled = 0
            dx = 0.0
            dy = 0.0
            dx_iFix = 0.0
            dy_iFix = 0.0
            x = 0.0
            y = 0.0
            quality = 0

        class Distance:
            dist = 0.0

        class IMU:
            acc_x = 0.0
            acc_y = 0.0
            acc_z = 0.0
            gyro_x = 0.0
            gyro_y = 0.0
            gyro_z = 0.0

        class Attitude:
            v0 = 0
            v1 = 0
            v2 = 0
            v3 = 0

        self.ofs = OfsData()
        self.distance = Distance()
        self.imu = IMU()
        self.attitude = Attitude()

        self.__threads = []
        self.__wait_for_hotplug = wait_for_hotplug
        self.__vendor_id = vendor_id
        self.__product_id = product_id

    def __open_device(self):
        target = None
        while target is None:
            target = find_device(self.__vendor_id, self.__product_id, 0)
            if target is None:
                if self.__wait_for_hotplug:
                    time.sleep(0.1)
                    continue
                else:
                    raise IOError('No ANOTC OFS device detected')

        self.open_path(target)

    def start(self):
        """
        Start the receiver threads and update data automatically.
        :return:
        """
        self.running = True
        self.__threads.append(threading.Thread(target=self.__thread_receiver))

        [ele.start() for ele in self.__threads]

    def kill(self):
        """
        Stop the receiver threads.
        :return:
        """
        self.running = False
        [ele.join() for ele in self.__threads]

    def __get_one_frame(self) -> Tuple[bool, int, int, bytes]:
        """
        get one frame of data from hid
        :return: tuple(<bool frame_ok>, <int addr>, <int func_id>, <bytes raw_data>)
        :rtype: (:obj:`bool`, :obj:`int`, :obj:`int`, :obj:`bytes`)
        """
        skip = False
        frame = None
        while not skip:
            try:
                frame = bytes(self.read(64))
                skip = True
            except Exception:
                self.close()
                self.ofs.quality = 0
                self.ofs.quality_decoupled = 0
                self.ofs.quality_raw = 0
                self.__open_device()

        # print(" ".join([frame.hex()[i] + frame.hex()[i+1] for i in range(0, len(frame.hex()), 2)]))
        try:
            f_len = frame[0]
            body = frame[1:f_len + 1]
            header, addr, func_id, d_len = body[0:4]
            data = body[4:4 + d_len]
            check_sum = body[4 + d_len]
            data_ok = True
            if header != 0xaa or sum(body[:-2]) == check_sum:
                data_ok = False
        except Exception:
            return False, 0, 0, b""

        return data_ok, addr, func_id, data

    def __thread_receiver(self):
        """
        receive and update data from hid
        :return:
        """
        while self.running:
            data_ok, addr, func_id, data = self.__get_one_frame()

            if data_ok and addr == self.addr:
                # if data ok and targeted

                # optical flow data
                if func_id == 0x51:
                    mode, state = data[0:2]
                    if not state:
                        continue
                    if mode == 0x00:
                        # raw ofs data
                        dx, dy, quality = struct.unpack("<bbB", data[2:])
                        self.ofs.dx_raw = dx
                        self.ofs.dy_raw = dy
                        if not state:
                            # set quality to 0 if sensor is not available
                            self.ofs.quality_raw = 0
                        else:
                            self.ofs.quality_raw = quality
                    elif mode == 0x01:
                        # decoupled ofs data
                        dx, dy, quality = struct.unpack("<hhB", data[2:])
                        self.ofs.dx_decoupled = dx
                        self.ofs.dy_decoupled = dy
                        if not quality:
                            # set quality to 0 if sensor is not available
                            self.ofs.quality_decoupled = 0
                        else:
                            self.ofs.quality_decoupled = quality
                    elif mode == 0x02:
                        # processed ofs data
                        dx, dy, dx_fix, dy_fix, integ_x, integ_y, quality = struct.unpack(
                            "<hhhhhhB", data[2:])
                        self.ofs.dx = dx
                        self.ofs.dy = dy
                        self.ofs.dx_iFix = dx_fix
                        self.ofs.dy_iFix = dy_fix
                        self.ofs.x = integ_x
                        self.ofs.y = integ_y
                        if not quality:
                            # set quality to 0 if sensor is not available
                            self.ofs.quality_decoupled = 0
                        else:
                            self.ofs.quality = quality

                # distance data
                elif func_id == 0x34:
                    distance = struct.unpack("<i", data[3:])[0]
                    self.distance.dist = distance

                # imu data
                elif func_id == 0x01:
                    acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z = struct.unpack("<hhhhhh", data[:-1])
                    self.ofs.acc_x = acc_x
                    self.ofs.acc_y = acc_y
                    self.ofs.acc_z = acc_z
                    self.ofs.gyro_x = gyro_x
                    self.ofs.gyro_y = gyro_y
                    self.ofs.gyro_z = gyro_z

                # attitude data
                elif func_id == 0x04:
                    v0, v1, v2, v3 = (struct.unpack("<hhhh", data[:-1]))
                    self.attitude.v0 = v0
                    self.attitude.v1 = v1
                    self.attitude.v2 = v2
                    self.attitude.v3 = v3


if __name__ == '__main__':
    import time

    sensor = AnoOpticalFlowSensor()
    sensor.start()
    try:
        while True:
            print("\rheight: {}, dx: {}, dy: {}, x: {}, y: {}, quality: {}            ".format(
                sensor.distance.dist, sensor.ofs.dx, sensor.ofs.dy, sensor.ofs.x, sensor.ofs.y, sensor.ofs.quality
            ), end="")
            time.sleep(0.1)
    except KeyboardInterrupt:
        sensor.kill()
