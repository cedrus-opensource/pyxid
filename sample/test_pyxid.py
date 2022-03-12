import pyxid2
import time

# get a list of all attached XID devices
devices = pyxid2.get_xid_devices()

dev = devices[0] # get the first device to use
print(dev)
dev.reset_base_timer()
dev.reset_rt_timer()

# If you're trying to collect responses from a StimTracker Duo/Quad,
# you'll have to enable USB output for the appropriate response type.
# You can read about it here https://cedrus.com/support/xid/commands.htm
# in the SIGNAL FILTERING & FLOW section.
#dev.enable_usb_output('K', True)

# Note that not all XID commands are implemented in this library. You
# can send any arbitrary string to the XID device if you need one of the
# unimplemented commands, like so (second arg is return bytes expected):
#dev._send_command('iuK1', 0)

if dev.is_response_device():
    print ("Press a key!")
    while not dev.has_response():
        dev.poll_for_response()

    response = dev.get_next_response()
    # You can filter out key releases by simply ignoring them
    if response['pressed'] == True:
        # Process response as desired
        print(response)

    dev.flush_serial_buffer()
    dev.clear_response_queue()

dev.set_pulse_duration(300)

sleep_flash = .3
for bm in range(0, 16):
    mask = 2 ** bm
    print("activate_line bitmask: ", mask)
    #dev.activate_line(lines=[1,3,5,7,9,11,13,15])
    dev.activate_line(bitmask=mask)

    time.sleep(sleep_flash)
