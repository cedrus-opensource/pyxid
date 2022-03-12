Python library for communicating with all Cedrus XID devices: StimTracker, RB-x40 response pads, c-pod, Lumina, and SV-1.

XID (eXperiment Interface Device) devices are used with software such as SuperLab, Presentation, and E-Prime for receiving input as part of stimulus/response testing experiments.

This handles all of the low level device handling for XID devices in python projects. The developer using this library must poll the attached device(s) for responses. 
Here's an example of how to do so, followed by an example of how to send a series of TTL signals:

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

The response is a python dict with the following keys:

    port: Device port the response was from (typically 0)
    key: Response pad key pressed by the subject
    pressed: True if the key was pressed, False if it was released
    time: value of the Response Time timer when the key was pressed/released

Sending a TTL pulse signal via the library can be done via the following methods:

    set_pulse_duration()
    activate_line()
    clear_line()

See the docstring for activate_line() for documentation on how to use it.

Response collection in pyxid

When a physical key is pressed on the device, a set of bytes describing it go into the serial buffer. This also occurs when the physical key is released. Calling poll_for_response(), makes pyxid check the serial buffer for bytes constituting a response packet, and put a response object in its internal response queue. It does so once per poll_for_response() call. Calling get_next_response() pops a single response from the response queue. If you want to avoid seeing more responses than necessary, you can use flush_serial_buffer() to prevent more responses from being added to the queue by poll_for_response(), and you can clear already processed responses with clear_response_queue().


Timers

Each XID device has an internal timer. This timer can be reset via a USB command or automatically on the onset of a light sensor or onset of audio.
