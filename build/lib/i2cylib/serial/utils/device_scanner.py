#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: I2cylib
# Filename: device_scanner
# Created on: 2022/8/27


from serial.tools.list_ports import comports


def getComDevice(keywords):
    """
    get serial ports within given keywords
    :param keywords: str (or List(str)), any of keyword matches description of a device would be return
    :return: List, a list of port(s) matches keywords
    """

    if not (isinstance(keywords, list) or isinstance(keywords, tuple)):
        keywords = [keywords]

    ports = comports(True)
    ports = [ele.device for ele in ports if sum([word in ele.description for word in keywords])]

    return ports
