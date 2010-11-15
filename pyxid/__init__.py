# -*- coding: utf-8 -*-

import pyxid

__all__ = ["get_xid_devices", "get_xid_device"]

def get_xid_devices():
    """
    Returns a list of all Xid devices connected to your computer.
    """
    devices = []
    scanner = pyxid.XidScanner()
    for i in range(scanner.device_count()):
        com = scanner.device_at_index(i)
        com.open()
        device = pyxid.XidDevice(com)
        devices.append(device)
    return devices


def get_xid_device(device_number):
    """
    returns device at a given index.

    Raises ValueError if the device at the passed in index doesn't
    exist.
    """
    scanner = pyxid.XidScanner()
    com = scanner.device_at_index(device_number)
    com.open()
    return pyxid.XidDevice(com)
