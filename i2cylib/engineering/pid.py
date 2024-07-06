#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: FFC_PC
# Filename: pid
# Created on: 2021/9/19


import time
import threading
import warnings

DOUBLE_PI = 6.283185307179586476925286766559


class PID(object):

    def __init__(self, kp: float = 1.0, ki: float = 0.0, kd: float = 0.0, core_freq: int = 50,
                 dterm_lpf_cutoff_hz: float = 20):
        """
        PID object

        :param kp: float (default: 0), K_P
        :param ki: float (default: 0), K_I
        :param kd: float (default: 0), K_D
        :param core_freq: int (>0, default: 50), set the expecting value of core frequency
        :param dterm_lpf_cutoff_hz: float (default: 20), set the cutoff frequency of D-Term LPF
        """
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.err = 0.0
        self.measures = 0.0
        self.expectation = 0.0
        self.out = 0.0
        self.offset = 0.0
        self.integ = 0.0

        self.death_area = 0

        self.err_limit = [0, 0]
        self.out_limit = [0, 0]
        self.integ_limit = [0, 0]

        self.dt = 1 / core_freq
        self.real_core_time = 0
        self.__time_offset = 0

        self.running = False
        self.thread_flags = {"thread_calculator": False}
        self.__out_t = 0

        self.debug_coreCanNotKeepUp = False
        self.__callback_funcs = []

        self.dterm_lpf_cutoff_hz = dterm_lpf_cutoff_hz
        self.__dterm_lpf_k = 0.0
        self.update_dterm_lpf()

        self.dterm_lpf_val = 0.0
        self.dterm_prev_mea = 0.0

    def update_dterm_lpf(self):
        """
        Update the D-Term LPF factor
        :return:
        """
        b = DOUBLE_PI * self.dterm_lpf_cutoff_hz * self.dt
        self.__dterm_lpf_k = b / (b + 1)

    def set_dterm_lpf_cutoff_freq(self, dterm_lpf_cutoff: float):
        """
        Set the D-Term LPF cutoff frequency and update the D-Term LPF factor immediately
        :param dterm_lpf_cutoff:
        :return:
        """
        self.dterm_lpf_cutoff_hz = dterm_lpf_cutoff
        self.update_dterm_lpf()

    def set_deltaT(self, dt):
        """
        Set the system loop time
        :param dt: float, seconds
        :return:
        """
        self.dt = dt
        self.update_dterm_lpf()

    def reset(self, kp=None, ki=None, kd=None):
        """
        Reset the PID system
        :param kp: float (default: None, means no changes), K_P
        :param ki: float (default: None, means no changes), K_I
        :param kd: float (default: None, means no changes), K_D
        :return:
        """
        self.out = 0.0
        self.offset = 0.0
        self.dterm_prev_mea = 0.0
        self.dterm_lpf_val = 0.0
        self.integ = 0.0

        if kp is not None:
            self.kp = kp
        if ki is not None:
            self.ki = ki
        if kd is not None:
            self.kd = kd

    def reset_i(self):
        """
        Reset I value
        :return:
        """
        self.integ = 0

    def calc(self, dt):
        """
        Calculate the PID
        :param dt:
        :return:
        """
        if dt <= 0:
            dt = 0.000001

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

        self.dterm_lpf_val += self.__dterm_lpf_k * (self.measures - self.dterm_lpf_val)
        deriv = (self.dterm_prev_mea - self.dterm_lpf_val) / dt
        self.dterm_prev_mea = self.dterm_lpf_val

        out = self.kp * self.err + self.ki * self.integ + self.kd * deriv

        if self.out_limit[0] != 0 or self.out_limit[1] != 0:
            if out > self.out_limit[1]:
                out = self.out_limit[1]
            elif out < self.out_limit[0]:
                out = self.out_limit[0]

        self.out = out

    def coreTask(self):
        """
        override this function to add core task
        :return:
        """
        for func in self.__callback_funcs:
            try:
                func(self)
            except Exception as e:
                warnings.warn("i2cylib.engineering.pid.coreTask callback failed: {}".format(e))

    def register_callback(self, callback_func: callable):
        """
        Register callback function that will be called in the PID uodate thread
        passing parameter: <PID this_pid_object>
        :param callback: callables
        :return:
        """
        self.__callback_funcs.append(callback_func)

    def remove_callback(self, callback_func: callable):
        """
        remove callback function that should be called in the PID uodate thread
        :return:
        """
        self.__callback_funcs.remove(callback_func)

    def __coreThread(self):
        if self.thread_flags["thread_calculator"]:
            return

        self.thread_flags["thread_calculator"] = True

        self.real_core_time = self.dt

        while self.running:
            ts = time.time()
            self.calc(self.real_core_time)
            self.coreTask()

            t = self.dt - time.time() + ts + self.__time_offset

            if t > 0:
                time.sleep(t)
            else:
                self.debug_coreCanNotKeepUp = True

            self.real_core_time = time.time() - ts
            self.__time_offset += 0.2 * (self.dt - self.real_core_time)

        self.thread_flags["thread_calculator"] = False

    def start(self):
        """
        开始计算PID

        :return:
        """
        if self.running:
            return
        self.running = True
        self.out = self.__out_t
        threading.Thread(target=self.__coreThread).start()

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

        self.__out_t = self.out
        self.out = 0

    def output(self):
        return self.out

    def input(self, measurement):
        self.measures = measurement

    def expect(self, expectation):
        self.expectation = expectation

    def debug(self):
        if not self.real_core_time:
            ct = 0
        else:
            ct = 1 / self.real_core_time
        return {"core_loop_time_ms": 1000 * self.real_core_time, "current_freq": ct, "time_offset": self.__time_offset}


class IncPID(PID):
    prev_err_2 = 0

    def calc(self, dt):
        self.err = self.expectation - self.measures + self.offset

        if -self.death_area < self.err < self.death_area:
            self.err = 0

        if self.err_limit[0] != 0 or self.err_limit[1] != 0:
            if self.err > self.err_limit[1]:
                self.err = self.err_limit[1]
            elif self.err < self.err_limit[0]:
                self.err = self.err_limit[0]

        self.integ = self.err * dt

        if self.integ_limit[0] != 0 or self.integ_limit[1] != 0:
            if self.integ > self.integ_limit[1]:
                self.integ = self.integ_limit[1]
            elif self.integ < self.integ_limit[0]:
                self.integ = self.integ_limit[0]

        deriv = (self.err - 2 * self.dterm_prev_mea + self.prev_err_2) / dt

        out = self.kp * self.err + self.ki * self.integ + self.kd * deriv

        if self.out_limit[0] != 0 or self.out_limit[1] != 0:
            if out > self.out_limit[1]:
                out = self.out_limit[1]
            elif out < self.out_limit[0]:
                out = self.out_limit[0]

        self.out += out

        self.prev_err_2 = self.dterm_prev_mea
        self.prev_err = self.err


def test(p=1.0, i=0.0, d=0.0,
         test_mass=4.0, gravity=10, noise_k=1, noise_a=10.0, measure_delay=0.1,
         test_exp_model=None, test_time=5, dt=0.02,
         start_hight=2, gamma=0.1, incpid=True, double_pid=False,
         p0=1.0, i0=0.0, d0=0.0, lpf_1_cutoff_hz=20.0, lpf_on=True):
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
    import numpy as np

    if incpid:
        pid = IncPID()
    else:
        pid = PID(dterm_lpf_cutoff_hz=3)
    pid.kp = p
    pid.ki = i
    pid.kd = d

    pid_2 = PID(dterm_lpf_cutoff_hz=200000)
    pid_2.kp = p0
    pid_2.ki = i0
    pid_2.kd = d0

    if test_exp_model is None:
        test_exp_model = [[0, 1]]

    lpf_b = 2 * np.pi * lpf_1_cutoff_hz * dt
    lpf_k = lpf_b / (1 + lpf_b)

    t = [0]
    exp = [0]
    exp_spd = [0]
    object_pos = [start_hight]
    obj_spd = [0]
    pid_out = [0]
    pos_mea = [0]

    speed_t = 0

    measures_pos = [start_hight for ele in range(int(measure_delay / dt))]
    measures_speed = [start_hight for ele in range(int(measure_delay / dt))]
    filtered_pos = [0]
    pid.dterm_prev_mea = measures_pos[0]

    out_prev_1 = 0
    out_prev_2 = 0

    # noise = np.random.normal(loc=0, size=int(test_time / dt + 10), scale=noise_k)
    # print(noise)

    if double_pid:
        pid.out_limit = (0, 2)
        pid_2.out_limit = (0, 100)
    else:
        pid.out_limit = (0, 100)

    # 生成长度为N的白噪声信号
    N = int(test_time / dt + 10)

    # 生成长度为N的蓝噪声信号
    alpha = noise_a
    f = np.linspace(0, 1, N // 2)
    P = f ** alpha
    P = np.concatenate((P, P[-1::-1]))
    X = np.fft.fft(np.random.normal(size=N, scale=5.0)) * np.sqrt(P)
    noise = np.real(np.fft.ifft(X))

    while True:
        t.append(t[-1] + dt)
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

        if double_pid:
            pid_2.expectation = exp_t
            if lpf_on:
                filtered_pos.append(filtered_pos[-1] + lpf_k * (measures_pos.pop(0) - filtered_pos[-1]))
                pid_2.measures = filtered_pos[-1]
            else:
                pid_2.measures = measures_pos.pop(0)
            pid_2.calc(dt)
            pid.expectation = pid_2.out
            exp_spd.append(pid_2.out)
            pid.measures = measures_speed.pop(0)
            obj_spd.append(pid.measures)
        else:
            pid.expectation = exp_t
            if lpf_on:
                filtered_pos.append(filtered_pos[-1] + lpf_k * (measures_pos.pop(0) - filtered_pos[-1]))
                pid.measures = filtered_pos[-1]
            else:
                pid.measures = measures_pos.pop(0)

        measures_pos.append(object_pos[-1] + noise_k * noise[len(t) - 1])
        pos_mea.append(object_pos[-1] + noise_k * noise[len(t) - 1])
        pid.calc(dt)

        pid_out.append(pid.out)

        out_prev_2 = pid.out - out_prev_1

        a = (pid_out[-1] - gravity) / test_mass
        speed_t += a * dt * 0.9
        measures_speed.append(speed_t)
        # speed_t = pid_out[-1] - gravity * test_mass
        speed_t -= gamma * speed_t
        pos_t = object_pos[-1] + speed_t * dt
        if pos_t < 0:
            pos_t = 0
        object_pos.append(pos_t)

    return t, exp, object_pos, pid_out, exp_spd, obj_spd, pos_mea, filtered_pos


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    from proplot import rc

    rc["style"] = "default"
    # 统一设置字体
    rc["font.family"] = "Times New Roman"
    # 统一设置轴刻度标签的字体大小
    rc['tick.labelsize'] = 18
    # 统一设置xy轴名称的字体大小
    rc["axes.labelsize"] = 22
    # 统一设置图例字体大小
    rc["legend.fontsize"] = 18
    # 统一设置轴刻度标签的字体粗细
    rc["axes.labelweight"] = "light"
    # 统一设置xy轴名称的字体粗细
    rc["tick.labelweight"] = "bold"

    # class modPID(PID):
    #     debug_coreTime = []
    #     debug_coreOffset = []
    #     debug_coreFreq = []
    #     debug_x = []
    #
    #     def coreTask(self):
    #         res = self.debug()
    #         self.debug_x.append(time.time())
    #         self.debug_coreFreq.append(res["current_freq"])
    #         self.debug_coreTime.append(res["core_loop_time_ms"])
    #         self.debug_coreOffset.append(1000 * res["time_offset"])
    #
    #
    # core_freq = 100
    # ctl = modPID(22.7016, 41.1049, 0.01, core_freq=core_freq)
    # ctl.measures = 0.01
    # ctl.expectation = 0.0
    # ctl.start()
    # time.sleep(2)
    # # ctl.measures = -0.01
    # # ctl.expectation = 0.0
    # # time.sleep(1)
    # # ctl.measures = 0.01
    # # ctl.expectation = 0.0
    # # time.sleep(2)
    # # ctl.measures = 0.0
    # # ctl.expectation = 0.0
    # # time.sleep(5)
    # print(ctl.debug())
    # print("Average core freq: {:.2f} Hz".format(len(ctl.debug_x) / (ctl.debug_x[-1] - ctl.debug_x[0])))
    # ctl.pause()
    # ctl.reset()
    #
    # x = [ele - ctl.debug_x[0] for ele in ctl.debug_x]
    # plt.subplot(211)
    # plt.plot(x, ctl.debug_coreFreq, color="red")
    # plt.plot(x, [core_freq for i in range(len(x))], color="blue")
    # plt.xlabel("t(s)")
    # plt.ylabel("Freq(Hz)")
    # plt.grid()
    # plt.legend("ep")
    # plt.subplot(212)
    # plt.plot(x, ctl.debug_coreOffset, color="green", alpha=0.6)
    # plt.legend("o")
    # plt.show()

    test_time = 10
    dt = 0.005

    x, exp, pos, out, spd_exp, spd_mea, pos_mea, filtered = test(p=6.5, i=3.0, d=3.3,
                                                                 test_mass=0.7,
                                                                 test_exp_model=[[1, 5],
                                                                                 # [2.5, 5],
                                                                                 # [5, 5],
                                                                                 # [7, 1],
                                                                                 # [9, 2],
                                                                                 ],
                                                                 test_time=test_time,
                                                                 dt=dt,
                                                                 measure_delay=0.10,
                                                                 noise_k=0,
                                                                 noise_a=0.5,
                                                                 gravity=10,
                                                                 gamma=0,
                                                                 incpid=False,
                                                                 start_hight=0,
                                                                 double_pid=True,
                                                                 p0=6.0, i0=3.0, d0=0.5,
                                                                 lpf_on=False, lpf_1_cutoff_hz=5)

    # plt.subplot(211)
    plt.plot(x, exp, color="red", label="expectation")
    plt.plot(x, pos, color="blue", label="actual_height")
    # plt.plot(x, filtered, color="green", alpha=1, label="measured_height")
    plt.xlabel("t(s)")
    plt.ylabel("Height(m)")
    plt.xlim([-0.02, 10.5])
    plt.ylim([0, 10])

    plt.legend()
    plt.grid(True, which="major")
    plt.subplots_adjust(left=0.12, right=0.95, top=0.95, bottom=0.15)
    plt.show()

    plt.plot(x, spd_exp, color='brown', label='speed_expectation')
    plt.plot(x, spd_mea, color='blue', label='speed_measure')
    plt.xlabel("t(s)")
    plt.ylabel("Speed(m/s)")

    plt.xlim([-0.02, 10.5])

    plt.legend()
    plt.grid(True, which="major")
    plt.subplots_adjust(left=0.12, right=0.95, top=0.95, bottom=0.15)

    plt.show()

    # plt.psd(pos_mea, NFFT=int(test_time / dt), Fs=1 / dt, color='blue')
    # # plt.title('Power Spectral Density')
    # plt.ylabel('Power (dB/Hz)')
    # plt.xlabel('Frequency (Hz)')
    # plt.ylim([-73, 7])
    # plt.xscale("log")
    #
    # plt.subplots_adjust(left=0.17, right=0.95, top=0.95, bottom=0.15)
    #
    # plt.show()

    # plt.psd(filtered, NFFT=int(test_time / dt), Fs=1 / dt, color='blue')
    # # plt.title('Power Spectral Density')
    # plt.ylabel('Power (dB/Hz)')
    # plt.xlabel('Frequency (Hz)')
    # plt.ylim([-73, 7])
    # plt.xscale("log")
    #
    # plt.subplots_adjust(left=0.17, right=0.95, top=0.95, bottom=0.15)
    #
    # plt.show()
