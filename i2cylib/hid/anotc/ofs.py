# !/usr/bin/env python3
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
import math

VENDOR_ID = 0x0483
PRODUCT_ID = 0xa022

__K_DEGREE = 180 / math.pi


def quaternion_to_euler_angles_math(quaternion, degrees=False):
    """
    Converts a quaternion to euler angles.
    :param quaternion: list()
    :param degrees: bool
    :return:
    """
    x, y, z, w = quaternion
    roll = math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
    pitch = math.asin(2 * (w * y - x * z))
    yaw = math.atan2(2 * (w * z + x * y), 1 - 2 * (z * z + y * y))
    if degrees:
        roll *= __K_DEGREE
        pitch *= __K_DEGREE
        yaw *= __K_DEGREE
    return roll, pitch, yaw


class AnoOpticalFlowSensor(hid.device):
    __TIMEOUT_SEC = 0.08

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
            x_ground = 0.0
            y_ground = 0.0
            quality = 0

            last_update_ts = 0

        class Distance:
            dist = 0.0
            height = 0.0
            height_relative = 0.0

            last_update_ts = 0

        class IMU:
            acc_x = 0.0
            acc_y = 0.0
            acc_z = 0.0
            gyro_x = 0.0
            gyro_y = 0.0
            gyro_z = 0.0

            last_update_ts = 0

        class Attitude:
            v0 = 0.0
            v1 = 0.0
            v2 = 0.0
            v3 = 1.0
            roll = 0.0
            pitch = 0.0
            yaw = 0.0
            offset_yaw = 0.0

            last_update_ts = 0

            def get_quaternion(self):
                return [self.v1, self.v2, self.v3, self.v0]

            def get_degrees_euler(self):
                return [self.roll * (180 / math.pi), self.pitch * (180 / math.pi), self.yaw * (180 / math.pi)]

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

    def reset_position_zero(self):
        """
        Reset the position zero on the device.
        :return:
        """
        self.ofs.x_ground = 0.0
        self.ofs.y_ground = 0.0

    def reset_yaw_direction_zero(self):
        """
        Reset the yaw direction zero on the device.
        :return:
        """
        self.attitude.offset_yaw = self.attitude.yaw

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
            if header != 0xaa or sum(body[:-2]) & 0xff != check_sum:
                data_ok = False
        except Exception:
            return False, 0, 0, b""

        return data_ok, addr, func_id, data

    def __thread_receiver(self):
        """
        receive and update data from hid
        :return:
        """

        last_x = 0.0
        last_y = 0.0
        real_acc_h_thresh = 20

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
                            self.ofs.quality = 0
                        else:
                            self.ofs.quality = quality
                        if time.time() - self.ofs.last_update_ts < self.__TIMEOUT_SEC:
                            dx = integ_x - last_x
                            if dx < -32768:
                                dx %= 65534
                            elif dx > 32767:
                                dx %= -65534
                            dy = integ_y - last_y
                            if dy < -32768:
                                dy %= 65534
                            elif dy > 32767:
                                dy %= -65534
                            yaw_angle = self.attitude.yaw - self.attitude.offset_yaw
                            cos_k = math.cos(yaw_angle)
                            sin_k = math.sin(yaw_angle)
                            self.ofs.x_ground += dx * cos_k + -dy * sin_k
                            self.ofs.y_ground += dx * sin_k + dy * cos_k
                        last_x = self.ofs.x
                        last_y = self.ofs.y
                        self.ofs.last_update_ts = time.time()  # update timestamp only when processed data received

                # distance data
                elif func_id == 0x34:
                    distance = struct.unpack("<i", data[3:])[0]
                    self.distance.dist = distance

                    if time.time() - self.attitude.last_update_ts < self.__TIMEOUT_SEC:
                        # decoupling height from distance
                        pitch_tan = 0.5 * math.pi - self.attitude.pitch
                        roll_tan = 0.5 * math.pi - self.attitude.roll
                        if pitch_tan != 0:
                            # preventing division by zero if pitch_tan == 0
                            pitch_tan = 1 / math.tan(pitch_tan) ** 2
                        if roll_tan != 0:
                            # preventing division by zero if pitch_tan == 0
                            roll_tan = 1 / math.tan(roll_tan) ** 2

                        last_height = self.distance.height
                        self.distance.height = distance * (1 / math.sqrt(1 + pitch_tan + roll_tan))
                        delta = self.distance.height - last_height
                        if delta > real_acc_h_thresh or delta < -real_acc_h_thresh:
                            delta = 0

                        self.distance.height_relative += delta
                        self.distance.last_update_ts = time.time()  # update timestamp only height decoupled

                # imu data
                elif func_id == 0x01:
                    acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z = struct.unpack("<hhhhhh", data[:-1])
                    self.imu.acc_x = acc_x
                    self.imu.acc_y = acc_y
                    self.imu.acc_z = acc_z
                    self.imu.gyro_x = gyro_x
                    self.imu.gyro_y = gyro_y
                    self.imu.gyro_z = gyro_z
                    self.imu.last_update_ts = time.time()

                # attitude data
                elif func_id == 0x04:
                    v = struct.unpack("<hhhh", data[:-1])
                    self.attitude.v0 = v[0] / 10000
                    self.attitude.v1 = v[1] / 10000
                    self.attitude.v2 = v[2] / 10000
                    self.attitude.v3 = v[3] / 10000
                    self.attitude.roll, self.attitude.pitch, self.attitude.yaw = quaternion_to_euler_angles_math(
                        self.attitude.get_quaternion()
                    )

                    self.attitude.last_update_ts = time.time()


if __name__ == '__main__':
    import time

    sensor = AnoOpticalFlowSensor()
    sensor.start()
    first = True
    time.sleep(0.5)
    sensor.reset_yaw_direction_zero()
    try:
        while True:
            if first:
                first = False
                t0 = time.time()
                d = sensor.attitude.get_quaternion()
                for i in range(1000000):
                    roll, pitch, yaw = quaternion_to_euler_angles_math(d)
                t1 = time.time() - t0
                print("q to euler using lib:math time spent: {:.2f}us, roll: {:.1f}, pitch: {:.1f}, yaw: {:.1f}".format(
                    t1, roll * (180 / math.pi), pitch * (180 / math.pi), yaw * (180 / math.pi)))

            print("\rheight: {}, dx: {}, dy: {}, x: {}, y: {}, x_ground: {:.1f}, y_ground:{:.1f}, quality: {}, roll:"
                  " {:.1f}, pitch: {:.1f}, yaw: {:.1f}, AccX: {}, AccY: {}, AccZ: {}, GyroX: {}, GyroY: {}, GyroZ: {}, height: {:.1f}cm, "
                  "height_relative: {:.1f}cm".format(
                sensor.distance.dist, sensor.ofs.dx, sensor.ofs.dy, sensor.ofs.x, sensor.ofs.y, sensor.ofs.x_ground,
                sensor.ofs.y_ground, sensor.ofs.quality, *sensor.attitude.get_degrees_euler(), sensor.imu.acc_x,
                sensor.imu.acc_y, sensor.imu.acc_z, sensor.imu.gyro_x, sensor.imu.gyro_y, sensor.imu.gyro_z,
                sensor.distance.height, sensor.distance.height_relative
            ), end="")
            time.sleep(0.2)
    except KeyboardInterrupt:
        sensor.kill()
