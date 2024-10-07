# -*- coding: utf-8 -*-

from .pyxid_impl import *  # noqa

scanner = XidScanner()

def get_xid_devices():
    """
    Returns a list of all Xid devices connected to your computer.
    """
    devices = []

    scanner.detect_xid_devices()

    for i in range(scanner.device_count()):
        com = scanner.device_at_index(i)
        if com.open():
            device = XidDevice(com)

            device.reset_timer()

            devices.append(device)
        else:
            continue
    return devices

def get_xid_device(device_number):
    print("The function get_xid_device() was removed in pyxid2 version 1.0.7. Use get_xid_devices() instead. Refer to https://github.com/cedrus-opensource/pyxid/tree/master/sample for usage examples.")
    return