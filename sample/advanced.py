'''
This is a sort of a work-in-progress sample containing commands not neccesary
in most uses of pyxid. Their use is highly situational at best.
'''

import pyxid2

# get a list of all attached XID devices
devices = pyxid2.get_xid_devices()

if devices:
    print(devices)
else:
    print("No XID devices detected")
    exit()

dev = devices[0] # get the first device to use
print(dev)

# If you're trying to collect responses from a StimTracker Duo/Quad,
# you'll have to enable USB output for the appropriate response type.
# You can read about it here https://cedrus.com/support/xid/commands.htm
# in the SIGNAL FILTERING & FLOW section.
# Note that this can also be easily accomplished by downloading Xidon from
# https://cedrus.com/support/xid/xidon.htm and going to Device -> Options
#dev.enable_usb_output('K', True)

# Note that not all XID commands are implemented in this library. You
# can send any arbitrary string to the XID device if you need one of the
# unimplemented commands, like so (second arg is return bytes expected):
#dev._send_command('iuK1', 0)