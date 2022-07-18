'''
This is a short sample of the Pulse Table feature of XID. Under the vast majority
of circumstances it's not necessary, and users are better served sending separate
event markers (see event_markers.py).
'''

import pyxid2
import time

# get a list of all attached XID devices
devices = pyxid2.get_xid_devices()

dev = devices[0] # get the first device to use
print(dev)

#dev.get_pulse_table_bitmask()
#dev.is_pulse_table_running()

dev.set_pulse_duration(0)
dev.set_lines(0xFFFF) #This is supposed to flash all lines, and will do so for 2 seconds before we set up the pulse table
time.sleep(2)

# Setting up the pulse table will reserve the lines used for pulse table use, so you will see those lines go low.
dev.clear_pulse_table()
dev.add_pulse_table_entry(0, 0x0101)
dev.add_pulse_table_entry(500, 0x0202)
dev.add_pulse_table_entry(1000, 0x0404)
dev.add_pulse_table_entry(1500, 0x0808)
dev.add_pulse_table_entry(2000, 0x0110)
dev.add_pulse_table_entry(2500, 0x0220)
dev.add_pulse_table_entry(3000, 0x0440)
dev.add_pulse_table_entry(3500, 0x0880)
dev.add_pulse_table_entry(4000, 0x0000)
dev.add_pulse_table_entry(0, 0x0000)
dev.run_pulse_table()
print("Waiting 5s for the pulse table to finish, as the bit mask cannot be cleared while it's running.")
# You could also end the program here and let the table run, but the sample is trying to avoid making lingering changes to the device.

time.sleep(5)
dev.set_lines(0x00)
dev.clear_pulse_table()