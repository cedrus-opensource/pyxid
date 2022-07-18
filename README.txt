Python library for communicating with all Cedrus XID devices: StimTracker, RB-x40 response pads, c-pod, Lumina, and SV-1.

XID (eXperiment Interface Device) devices are used with software such as SuperLab, Presentation, and E-Prime for receiving input as part of stimulus/response testing experiments. This handles all of the low level device handling for XID devices in python projects.

Minimal samples for collecting responses and sending event markers are available in the Git repo.

------
Response collection in pyxid

When a physical key is pressed on the device, a set of bytes describing it go into the serial buffer. This also occurs when the physical key is released. Calling poll_for_response() makes pyxid check the serial buffer for bytes constituting a response packet, and put a response object in its internal response queue. It does so once per poll_for_response() call. Calling get_next_response() pops a single response from the response queue. If you want to avoid seeing more responses than necessary, you can use flush_serial_buffer() to prevent more responses from being added to the queue by poll_for_response(), and you can clear already processed responses with clear_response_queue().

The response object is a python dict with the following keys:

    port: Device port the response was from (typically 0)
    key: Response pad key pressed by the subject
    pressed: True if the key was pressed, False if it was released
    time: value of the Response Time timer when the key was pressed/released

For an example see sample/responses.py

------
Sending a TTL pulse signal via the library can be done via the following methods:

    set_pulse_duration()
    activate_line()
    clear_line()
    clear_all_lines()

For an example see sample/event_markers.py

------
Timers

Each XID device has an internal timer. This timer can be reset via reset_timer() or automatically on the onset of a light sensor or onset of audio. It's commonplace to reset the timer at the start of the experiment and/or at the onset of a simulus.
