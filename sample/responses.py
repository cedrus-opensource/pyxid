'''
This sample shows how to collect responses from an XID device. Note that you 
have to poll the device for responses manually (done in a while loop here).

When a physical key is pressed on the device, a set of bytes describing it go
into the serial buffer. This also occurs when the physical key is released.
Calling poll_for_response() makes pyxid check the serial buffer for bytes
constituting a response packet, and put a response object in its internal
response queue. It does so once per poll_for_response() call. Calling
get_next_response() pops a single response from the response queue. If you want
to avoid seeing more responses than necessary, you can use
flush_serial_buffer() to prevent more responses from being added to the queue
by poll_for_response(), and you can clear already processed responses with
clear_response_queue().
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

dev.reset_timer()

print ("Press a key!")
while not dev.has_response():
    dev.poll_for_response()

response = dev.get_next_response()
# You can filter out key releases by simply ignoring them
if response['pressed'] == True:
    # Process response as desired
    print(response)
    # response is a python dict with the following keys:
    #  port: Device port the response was from (typically 0)
    #  key: Response pad key pressed by the subject
    #  pressed: True if the key was pressed, False if it was released
    #  time: value of the Response Time timer when the key was pressed/released

dev.flush_serial_buffer()
dev.clear_response_queue()
