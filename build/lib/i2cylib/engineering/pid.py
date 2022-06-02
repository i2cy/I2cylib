#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: FFC_PC
# Filename: pid
# Created on: 2021/9/19


import time
import threading


class PID(object):

    def __init__(self, kp=0, ki=0, kd=0, core_freq=50):
        """
        PID object

        :param kp: float (default: 0), K_P
        :param ki: float (default: 0), K_I
        :param kd: float (default: 0), K_D
        :param core_freq: int (>0, default: 50), set the expecting value of core frequency
        """
        self.kp = 0
        self.ki = 0
        self.kd = 0
        self.err = 0
        self.measures = 0
        self.expectation = 0
        self.out = 0
        self.offset = 0
        self.prev_err = 0
        self.integ = 0

        self.death_area = 0

        self.err_limit = [0, 0]
        self.out_limit = [0, 0]
        self.integ_limit = [0, 0]

        self.dt = 1 / core_freq
        self.__core_time = 0
        self.__time_offset = 0

        self.running = False
        self.thread_flags = {"thread_calculator": False}

    def set_deltaT(self, dt):
        self.dt = dt

    def reset(self, kp=0, ki=0, kd=0):
        self.out = 0
        self.offset = 0
        self.prev_err = 0
        self.integ = 0

    def reset_i(self):
        self.integ = 0

    def calc(self, dt):
        self.err = self.expectation - self.measures + self.offset

        if -self.death_area < self.err < self.death_area:
            self.err = 0

        if self.err_limit[0] != 0 or self.err_limit[1] != 0:
            if self.err > self.err_limit[1]:
                self.err = self.err_limit[1]
            elif self.err < self.err_limit[0]:
                self.err = self.err_limit[0]

        self.integ += self.err * dt

        if self.integ_limit[0] != 0 or self.integ_limit[1] != 0:
            if self.integ > self.integ_limit[1]:
                self.integ = self.integ_limit[1]
            elif self.integ < self.integ_limit[0]:
                self.integ = self.integ_limit[0]

        deriv = (self.prev_err - self.measures) / dt

        out = self.kp * self.err + self.ki * self.integ + self.kd * deriv

        if self.out_limit[0] != 0 or self.out_limit[1] != 0:
            if out > self.out_limit[1]:
                out = self.out_limit[1]
            elif out < self.out_limit[0]:
                out = self.out_limit[0]

        self.out = out

        self.prev_err = self.measures

    def __thread_calculator(self):
        if self.thread_flags["thread_calculator"]:
            return

        self.thread_flags["thread_calculator"] = True

        while self.running:
            ts = time.time()
            self.calc(self.dt + self.__time_offset)
            t = self.dt - time.time() + ts + self.__time_offset
            if t > 0:
                time.sleep(t)
            self.__core_time = time.time() - ts
            self.__time_offset += 0.2 * (self.dt - self.__core_time)

        self.thread_flags["thread_calculator"] = False

    def start(self):
        """
        开始计算PID

        :return:
        """
        if self.running:
            return
        self.running = True
        threading.Thread(target=self.__thread_calculator).start()

    def pause(self, wait=False):
        """
        暂停计算PID

        :return:
        """
        self.running = False
        while wait:
            wait = False
            for i in self.thread_flags.keys():
                if self.thread_flags[i]:
                    wait = True

    def debug(self):
        if not self.__core_time:
            ct = 0
        else:
            ct = 1 / self.__core_time
        return {"current_freq": ct, "time_offset": self.__time_offset}


def test(p=1.0, i=0.0, d=0.0, test_mass=4.0, gravity=10, noise_k=1, test_exp_model=None, test_time=5, dt=0.02):
    """
    pid test run, test object moving in single axis, start in x=0, F=10*pid.out

    :param p: float, kp
    :param i: float, ki
    :param d: float, kd
    :param test_mass: the object mass in test environment
    :param
    :param test_exp_model: [list_time, list_value], example [[0, 0], [0.2, 1], [1.2, 0]] for f(t)=u(t-0.2)-u(t-1.2)
    :param test_time: int, test time
    :return: list(t), list(exp), list(object_pos), list(pid_out)
    """

    import random
    pid = PID()
    pid.kp = p
    pid.ki = i
    pid.kd = d

    if test_exp_model is None:
        test_exp_model = [[0, 1]]

    t = [0]
    exp = [0]
    object_pos = [0]
    pid_out = [0]

    speed_t = 0

    while True:
        t.append(t[-1]+dt)
        if t[-1] > test_time:
            t.pop(-1)
            break

        step = 0
        for i in test_exp_model:
            if t[-1] > i[0]:
                step += 1
        if step >= len(test_exp_model):
            step -= 1
        exp_t = test_exp_model[step][1]
        exp.append(exp_t)

        pid.expectation = exp_t
        pid.measures = object_pos[-1] + noise_k * random.random()
        pid.calc(dt)
        pid_out.append(pid.out)

        a = (10 * pid_out[-1] - gravity) / test_mass
        speed_t += a * dt * 0.9
        pos_t = object_pos[-1] + speed_t * dt
        object_pos.append(pos_t)

    return t, exp, object_pos, pid_out


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    x, exp, pos, out = test(p=70.0, i=130, d=4,
                            test_mass=2.2,
                            test_exp_model=[[0, 5],
                                            [2.5, 5],
                                            [5, 0],
                                            [7, 1],
                                            [9, 2],
                                            ],
                            test_time=10,
                            dt=0.01,
                            noise_k=0.4,
                            gravity=10)

    plt.plot(x, exp, color="red")
    plt.plot(x, pos, color="blue")
    #plt.plot(x, out, color="green")
    plt.legend("epo")
    plt.show()


