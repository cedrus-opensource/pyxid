Python library for interfacing with Cedrus XID and StimTracker devices

XID (eXperiment Interface Device) devices are used in software such as
SuperLab, Presentation, and ePrime for receiving input as part of
stimulus/response testing experiments.

This handles all of the low level device handling for XID devices in
python projects.  The developer using this library must poll the
attached device(s) for responses.  Here's an example of how to do so:

    import pyxid

    # get a list of all attached XID devices
    devices = pyxid.get_xid_devices()

    dev = devices[0] # get the first device to use
    if dev.is_response_device():
        dev.reset_base_timer()
        dev.reset_rt_timer()

        while True:
            dev.poll_for_response()
            if dev.response_queue_size() > 0:
                response = dev.get_next_response()
                # do something with the response


The response is a python dict with the following keys:

    pressed: True if the key was pressed, False if it was released
    key: Response pad key pressed by the subject
    port: Device port the response was from (typically 0)
    time: value of the Response Time timer when the key was hit/released


StimTracker

Support for Cedrus StimTracker devices is now included.  On StimTracker
devices, there are the following methods:

    set_pulse_duration()
    activate_line()
    clear_line()

See the docstring for activate_line() for documentation on how to use it.

These methods are not available if the device is a response pad.

StimTracker is used in software such as SuperLab, Presentation and ePrime
for sending event markers.


Timers

Each Cedrus XID device has an internal timer a Base Timer and a
Response Time Timer.  The Base Timer should be reset at the start of
an experiment.  The Response Time timer should be reset whenever a
stimulus is presented.

At the time of this library release, there is a known issue with clock
drift in XID devices.  Our hardware/firmware developer is currently
looking into the issue.  

Given the issue, use of the response timer built into the response
pads is optional.  If you wish to use the time reported from the
response pads, do the following after importing the pyxid library:

    import pyxid
    pyxid.use_response_pad_timer = True

This will return the time in the 'time' field of the dict returned by
XidDevice.get_next_response(), otherwise, the 'time' field will
contain 0.

Windows Specific Issues

Sometimes, windows fails at detecting XID devices.  Running
detect_xid_devices() a second time should result in finding the
devices.
