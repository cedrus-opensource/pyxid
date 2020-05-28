import pyxid2
import time

# get a list of all attached XID devices
devices = pyxid2.get_xid_devices()

dev = devices[0] # get the first device to use
print(dev)
dev.reset_base_timer()
dev.reset_rt_timer()

#dev._send_command('iuA1', 0)
#dev.enable_usb_output('K', True)

if dev.is_response_device():
    print ("Press a key!")
    while not dev.has_response():
        dev.poll_for_response()

    response = dev.get_next_response()
    print(response)
    dev.clear_response_queue()

dev.set_pulse_duration(300)

sleep_flash = .3
for bm in range(0, 16):
    mask = 2 ** bm
    print("activate_line bitmask: ", mask)
    #dev.activate_line(lines=[1,3,5,7,9,11,13,15])
    dev.activate_line(bitmask=mask)

    time.sleep(sleep_flash)
