# -*- coding: utf-8 -*-
from struct import pack
from struct import unpack

from .constants import NO_KEY_DETECTED
from .internal import XidConnection
from .keymaps import (rb_530_keymap, rb_730_keymap, rb_830_keymap,
                      rb_834_keymap, lumina_keymap)

import ftd2xx

class XidScanner(object):
    """
    Scan the computer for connected XID devices
    """
    def __init__(self):
        self.__xid_cons = []
        self.detect_xid_devices()

    def detect_xid_devices(self):
        """
        For all of the com ports connected to the computer, send an
        XID command '_c1'.  If the device response with '_xid', it is
        an xid device.
        """
        self.__xid_cons = []

        devs = ftd2xx.listDevices()

        if devs is None:
            return

        for d in devs:
            device_found = False
            for b in [115200, 19200, 9600, 57600, 38400]:
                con = XidConnection(d, b)

                if con.open():
                    con.flush()
                
                    try:
                        returnval = con.send_xid_command("_c1", 5).decode('ASCII')
                    except UnicodeDecodeError as e:
                        # Assume this isn't an XID device, since it returned something weird.
                        con.close()
                        break

                    if returnval.startswith('_xid'):
                        device_found = True
                        self.__xid_cons.append(con)

                        if(returnval != '_xid0'):
                            # set the device into XID mode
                            con.send_xid_command('c10')
                            con.flush()

                    con.close()
                    if device_found:
                        # Device found, we're done.
                        break
                else:
                    continue

    def device_at_index(self, index):
        """
        Returns the device at the specified index
        """
        if index >= len(self.__xid_cons):
            raise ValueError("Invalid device index")

        return self.__xid_cons[index]

    def device_count(self):
        """
        Number of XID devices connected to the computer
        """
        return len(self.__xid_cons)


class XidError(Exception):
    pass


class XidDevice(object):
    """
    Class for interfacing with a Cedrus XID device.

    At the beginning of an experiment, the developer should call:

        XidDevice.reset_base_timer()

    Whenever a stimulus is presented, the developer should call:

        XidDevice.reset_rt_timer()
    """

    def __init__(self, xid_connection):
        self.con = xid_connection
        self._impl = None
        self.product_id = -1
        self.model_id = -1
        self.major_fw_version = -1
        self.device_name = 'Uninitialized XID device'
        self.keymap = None
        self.response_queue = []
        
        self.init_device()

        self.con.set_using_stim_tracker_output(self.major_fw_version == 2 or self.product_id == b'S')
        self.con.set_resp_packet_size(self.major_fw_version == 2 and self.product_id == b'S')
        if self.major_fw_version == 1:
            self.con.send_xid_command('a10')
        self.con.clear_digital_output_lines(0xff)

    def __del__(self):
        self.con.close()
        del self.con

    def reset_rt_timer(self):
        """
        Resets the Reaction Time timer.
        """
        self.con.send_xid_command("e5")

    def reset_base_timer(self):
        """
        Resets the base timer
        """
        if self.major_fw_version < 2:
            self.con.send_xid_command("e1")

    def query_base_timer(self):
        """
        gets the value from the device's base timer
        """
        time = -1
        if self.major_fw_version < 2:
            (_, _, time) = unpack('<ccI', self.con.send_xid_command("e3", 6))
        
        return time

    def is_response_device(self):
        """
        "Response device" is used loosely here. Second generation StimTrackers are not response
        devices in a strict sense, they are capable of reporting keypresses via USB.
        The only devices you will never get a keypress from are first gen StimTrackers and c-pods.
        """
        return not (self.product_id == b'S' and self.major_fw_version != 2) and self.product_id != b'4'

    def init_device(self):
        """
        Initializes the device with the proper keymaps and name
        """
        self.product_id = self._send_command('_d2', 1)
        self.model_id = self._send_command('_d3', 1)
        self.major_fw_version = int(self._send_command('_d4', 1))

        if self.product_id == b'0':
            self.device_name = 'Cedrus Lumina 3G' if self.major_fw_version == 2 else 'Cedrus Lumina LP-400'
            self.keymap = lumina_keymap
        elif self.product_id == b'1':
            self.device_name = 'Cedrus SV-1 Voice Key'
        elif self.product_id == b'2':
            if self.model_id == b'1':
                self.device_name = 'Cedrus RB-540' if self.major_fw_version == 2 else 'Cedrus RB-530'
                self.keymap = rb_530_keymap
            elif self.model_id == b'2':
                self.device_name = 'Cedrus RB-740' if self.major_fw_version == 2 else 'Cedrus RB-730'
                self.keymap = rb_730_keymap
            elif self.model_id == b'3':
                self.device_name = 'Cedrus RB-840' if self.major_fw_version == 2 else 'Cedrus RB-830'
                self.keymap = rb_830_keymap
            elif self.model_id == b'4':
                self.device_name = 'Cedrus RB-844' if self.major_fw_version == 2 else 'Cedrus RB-834'
                self.keymap = rb_834_keymap
            else:
                raise XidError('Unknown RB Device')
        elif self.product_id == b'4':
            self.device_name = 'Cedrus C-POD'
        elif self.product_id == b'S':
            if self.major_fw_version < 2:
                self.device_name = 'Cedrus StimTracker'
            else:
                self.device_name = 'Cedrus StimTracker Duo' if self.model_id == b'1' else 'Cedrus StimTracker Quad'

        elif self.product_id == -99:
            raise XidError('Invalid XID device')

    def _send_command(self, command, expected_bytes):
        """
        Send an XID command to the device
        """
        response = self.con.send_xid_command(command, expected_bytes)

        return response

    def poll_for_response(self):
        """
        Polls the device for user input

        If there is a keymapping for the device, the key map is applied
        to the key reported from the device. This only applies to port 0
        (typically the physical buttons) responses. Rest are unchanged.

        If a response is waiting to be processed, the response is appended
        to the internal response_queue
        """
        key_state = self.con.check_for_keypress()

        if key_state != NO_KEY_DETECTED:
            response = self.con.get_current_response()

            if response['port'] == 0:
                if self.keymap is not None:
                    response['key'] = self.keymap[response['key']]
                else:
                    response['key'] -= 1

            self.response_queue.append(response)

    def response_queue_size(self):
        """
        Number of responses in the response queue
        """
        return len(self.response_queue)

    def has_response(self):
        """
        Do we have responses in the queue
        """
        return len(self.response_queue) > 0

    def get_next_response(self):
        """
        Pops the response at the beginning of the response queue
        and returns it.

        This function returns a dict object with the following keys:

            pressed:  A boolean value of whether the event was a keypress
                      or key release.
            key:      The key on the device that was pressed.  This is a
                      0 based index.
            port:     Device port the response came from.  Typically this
                      is 0 on RB-series devices, and 2 on SV-1 voice key
                      devices.
            time:     For the time being, this just returns 0.  There is
                      currently an issue with clock drift in the Cedrus XID
                      devices.  Once we have this issue resolved, time will
                      report the value of the RT timer in miliseconds.
        """
        response = None
        if self.has_response():
            response = self.response_queue.pop(0)
        return response

    def clear_response_queue(self):
        """
        Clears the response queue
        """
        self.response_queue = []

    # Will flush both input and output buffers by default.
    # 1 is output (from device) only, 2 is input (to device) only
    def flush_serial_buffer(self, mask=0):
        self.con.flush(mask)

    def set_pulse_duration(self, duration):
        """
        Sets the pulse duration for events in miliseconds when activate_line
        is called
        """
        if duration > 4294967295:
            raise ValueError('Duration is too long. Please choose a value '
                             'less than 4294967296.')

        big_endian = hex(duration)[2:]
        if len(big_endian) % 2 != 0:
            big_endian = '0'+big_endian

        little_endian = []

        for i in range(0, len(big_endian), 2):
            little_endian.insert(0, big_endian[i:i+2])

        for i in range(0, 4-len(little_endian)):
            little_endian.append('00')

        command = 'mp'
        for i in little_endian:
            command += chr(int(i, 16))

        self.con.send_xid_command(command, 0)

    def activate_line(self, lines=None, bitmask=None, leave_remaining_lines=False):
        """
        Triggers an output line.

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
        0 and 255 where 0 specifies no lines, and 255 is all lines.  For a
        mapping between lines and their bit values, see the `_lines` class
        variable.

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
        if lines is None and bitmask is None:
            raise ValueError('Must set one of lines or bitmask')
        if lines is not None and bitmask is not None:
            raise ValueError('Can only set one of lines or bitmask')

        if bitmask is not None:
            if bitmask not in list(range(0, 65536)):
                raise ValueError('bitmask must be an integer between '
                                 '0 and 65535')

        if lines is not None:
            if not isinstance(lines, list):
                lines = [lines]

            bitmask = 0
            for l in lines:
                if l < 1 or l > 16:
                    raise ValueError('Line numbers must be between 1 and 16 '
                                     '(inclusive)')
                bitmask |= 2 ** (l-1)

        self.con.set_digital_output_lines(bitmask, leave_remaining_lines)

    # A more straightforward function for raising lines. You tell it the mask you want to see
    # and it sets it.
    def set_lines(self, lines):
        self.con.set_digio_lines_to_mask(lines)

    def clear_line(self, lines=None, bitmask=None, leave_remaining_lines=False):
        """
        The inverse of activate_line.  If a line is active, it deactivates it.

        This has the same parameters as activate_line()
        """
        if lines is None and bitmask is None:
            raise ValueError('Must set one of lines or bitmask')
        if lines is not None and bitmask is not None:
            raise ValueError('Can only set one of lines or bitmask')

        if bitmask is not None:
            if bitmask not in list(range(0, 65536)):
                raise ValueError('bitmask must be an integer between '
                                 '0 and 65535')

        if lines is not None:
            if not isinstance(lines, list):
                lines = [lines]

            bitmask = 0
            for l in lines:
                if l < 1 or l > 16:
                    raise ValueError('Line numbers must be between 1 and 16 '
                                     '(inclusive)')
                bitmask |= 2 ** (l-1)

        self.con.clear_digital_output_lines(bitmask, leave_remaining_lines)

    def enable_usb_output(self, selector, enable):
        if self.major_fw_version < 2:
            return

        command = 'iu%s%s' % (selector, '1' if enable is True else '0')
        self.con.send_xid_command(command, 0)

    def get_pulse_table_bitmask(self):
        lines = 0
        if self.major_fw_version > 1:
            (_, _, _, lines) = unpack('<cccH', self.con.send_xid_command("_mk", 5))

        return lines

    def set_pulse_table_bitmask(self, mask):
        ptable_mask = pack('<ccH', b'm', b'k', mask)
        if self.major_fw_version > 1:
            self.con.send_xid_byte_command(ptable_mask)

    def clear_pulse_table(self):
        if self.major_fw_version > 1:
            self.con.send_xid_command("mc")

    def is_pulse_table_running(self):
        running = -1
        if self.major_fw_version > 1:
            (_, _, _, running) = unpack('<cccc', self.con.send_xid_command("_mr", 4))

        return running == b'1'

    def run_pulse_table(self):
        if self.major_fw_version > 1:
            self.con.send_xid_command("mr")

    def stop_pulse_table(self):
        if self.major_fw_version > 1:
            self.con.send_xid_command("ms")

    def add_pulse_table_entry(self, time, mask):
        ptable_mask = pack('<ccIH', b'm', b't', time, mask)
        if self.major_fw_version > 1:
            self.con.send_xid_byte_command(ptable_mask)

    def reset_output_lines(self):
        if self.major_fw_version > 1:
            self.con.send_xid_command("mz")

    def __getattr__(self, attrname):
        return getattr(self._impl, attrname)

    def __str__(self):
        return '<XidDevice "%s">' % self.device_name

    def __repr__(self):
        return self.__str__()
