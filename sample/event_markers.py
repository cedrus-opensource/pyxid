'''
This sample outputs 8 event markers using an XID device on lines 1 through 8
at 300ms intervals, producing what we call "marching lights".
'''
import pyxid2
import time

# get a list of all attached XID devices
devices = pyxid2.get_xid_devices()

if devices:
    print(devices)
else:
    print("No XID devices detected")
    exit()

dev = devices[0] # get the first device to use

print("Using ", dev)

#Setting the pulse duration to 0 makes the lines stay activated until lowered
#manually with clear_line() or clear_all_lines().
dev.set_pulse_duration(300)

for line in range(1, 9):
    print("raising line {} (bitmask {})".format(line, 2 ** (line-1)))
    dev.activate_line(lines=line)
    time.sleep(.3)

dev.clear_all_lines()


"""
Here is the full description of activate_line() and clear_line():

activate_line() triggers an output line. clear_line() is the
inverse of activate_line. If a line is active, it deactivates it.
It has the same parameters as activate_line().

There are up to 16 output lines on XID devices that can be raised
in any combination.  To raise lines 1 and 7, for example, you pass
in the list: activate_line(lines=[1, 7]).

To raise a single line, pass in just an integer, or a list with a
single element to the lines keyword argument:

    activate_line(lines=3)

    or

    activate_line(lines=[3])

The `lines` argument must either be an Integer, list of Integers, or
None.

If you'd rather specify a bitmask for setting the lines, you can use
the bitmask keyword argument.  Bitmask must be a Integer value between
0 and 255 where 0 specifies no lines, and 255 is all lines (65535 if
using 16 lines of output).

To use this, call the function as so to activate lines 1 and 6:

    activate_line(bitmask=33)

leave_remaining_lines tells the function to only operate on the lines
specified.  For example, if lines 1 and 8 are active, and you make
the following function call:

    activate_line(lines=4, leave_remaining_lines=True)

This will result in lines 1, 4 and 8 being active.

If you call activate_line(lines=4) with leave_remaining_lines=False
(the default), if lines 1 and 8 were previously active, only line 4
will be active after the call.
"""