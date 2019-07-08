Python library for communicating with all Cedrus XID devices: StimTracker, RB-x40 response pads, c-pod, Lumina, and SV-1.

XID (eXperiment Interface Device) devices are used with software such as SuperLab, Presentation, and E-Prime for receiving input as part of stimulus/response testing experiments.

This handles all of the low level device handling for XID devices in python projects. The developer using this library must poll the attached device(s) for responses. 
Here's an example of how to do so, followed by an example of how to send a series of TTL signals:

    import pyxid
    import time

    # get a list of all attached XID devices
    devices = pyxid.get_xid_devices()

    dev = devices[0] # get the first device to use
    print(dev)
    dev.reset_base_timer()
    dev.reset_rt_timer()

    if dev.is_response_device():
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

The response is a python dict with the following keys:

    pressed: True if the key was pressed, False if it was released
    key: Response pad key pressed by the subject
    port: Device port the response was from (typically 0)
    time: value of the Response Time timer when the key was hit/released


Sending a TTL pulse signal via the library can be done via the following methods:

    set_pulse_duration()
    activate_line()
    clear_line()

See the docstring for activate_line() for documentation on how to use it.


Timers

Each XID device has an internal timer. This timer can be reset via a USB command or automatically on the onset of a light sensor or onset of audio.
