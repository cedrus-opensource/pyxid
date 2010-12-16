#!/usr/bin/env python
from __future__ import print_function
import pyxid
import time

def main():
    device = pyxid.get_xid_devices()[0]

    if device.is_response_device():
        device.reset_base_timer()
        device.reset_rt_timer()
        start_time = int(time.time()*1000)

        print('Testing device: %s' % device.device_name)
        fw_major = int(device._send_command('_d4', 1))
        fw_minor = int(device._send_command('_d5', 1))
        print('Firmware version: %d.%d' % (fw_major, fw_minor))
        print('{:<24} {:>10} {:>13} {:>14}'.format(
            'Wall Time',
            'RT time',
            'Elapsed Time',
            'Difference'))
        while True:
            device.poll_for_response()
            if device.response_queue_size() > 0:
                response = device.get_next_response()
                if response['pressed']:
                    res_time = int(time.time()*1000)
                    elapsed = res_time - start_time
                    diff = response['time'] - elapsed
                    wall_time = time.ctime()
                    print('{:<24} {:>10} {:>13} {:>14}'.format(
                        wall_time,
                        response['time'],
                        elapsed,
                        diff))



if __name__ == '__main__':
    main()
