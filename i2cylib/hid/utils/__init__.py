#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: I2cylib
# Filename: __init__.py
# Created on: 2024/4/27

import hid


def find_device(vendor_id: int, product_id: int, interface_number=None) -> str:
    """
    Find a HID device by its ID and product ID.
    :param vendor_id: vendor ID
    :type vendor_id: int
    :param product_id: product ID
    :type product_id: int
    :param interface_number: interface number, default to None which means no specific interface number
    :type interface_number: int, optional
    :return: path of HID device
    :rtype: str
    """
    target = None
    for ele in hid.enumerate():
        if ele["vendor_id"] == vendor_id and ele["product_id"] == product_id:
            if interface_number is not None and ele['interface_number'] == interface_number:
                target = ele['path']
    return target
