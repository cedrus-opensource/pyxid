# -*- coding: utf-8 -*-

from pyxid_impl import *

# Flag for whether or not the response pad timer value should be
# returned from XidDevice.get_next_response()
#
# Set this to true if you want to return the time reported by the
# response pad.  See the README file for reasons you may not want to
# do this.
use_response_pad_timer = False

def get_xid_devices():
    """
    Returns a list of all Xid devices connected to your computer.
    """
    devices = []
    scanner = XidScanner()
    for i in range(scanner.device_count()):
        com = scanner.device_at_index(i)
        com.open()
        device = XidDevice(com)
        devices.append(device)
    return devices


def get_xid_device(device_number):
    """
    returns device at a given index.

    Raises ValueError if the device at the passed in index doesn't
    exist.
    """
    scanner = XidScanner()
    com = scanner.device_at_index(device_number)
    com.open()
    return XidDevice(com)


def test_event_loop(devices):
    for d in devices:
        d.reset_base_timer()
        d.reset_rt_timer()

    while True:
        for d in devices:
            if d.is_response_device():
                d.poll_for_response()

                if d.response_queue_size() > 0:
                    print d.device_name, d.get_next_response()

