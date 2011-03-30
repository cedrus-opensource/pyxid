# -*- coding: utf-8 -*-
from serial_wrapper import SerialPort
from serial.serialutil import SerialException
from struct import unpack
from constants import NO_KEY_DETECTED
from internal import XidConnection
from keymaps import rb_530_keymap, rb_730_keymap, rb_830_keymap, rb_834_keymap, \
     lumina_keymap


class XidScanner(object):
    """
    Scan the computer for connected XID devices
    """
    def __init__(self):
        self.__com_ports = SerialPort.available_ports()
        self.__xid_cons = []
        self.detect_xid_devices()


    def detect_xid_devices(self):
        """
        For all of the com ports connected to the computer, send an
        XID command '_c1'.  If the device response with '_xid', it is
        an xid device.
        """
        self.__xid_cons = []

        for c in self.__com_ports:
            device_found = False
            for b in [115200, 19200, 9600, 57600, 38400]:
                if device_found:
                    break

                con = XidConnection(c, b)

                try:
                    con.open()
                except SerialException:
                    continue

                con.flush_input()
                con.flush_output()
                returnval = con.send_xid_command("_c1", 5)

                if returnval.startswith('_xid'):
                    device_found = True
                    self.__xid_cons.append(con)

                    if(returnval != '_xid0'):
                        # set the device into XID mode
                        con.send_xid_command('c10')
                        con.flush_input()
                        con.flush_output()
                con.close()


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


class BaseDevice(object):
    def __init__(self, connection, name="Unknown XID Device"):
        self.con = connection
        self.device_name = name

    def reset_rt_timer(self):
        """
        Resets the Reaction Time timer.
        """
        self.con.send_xid_command("e5")


    def reset_base_timer(self):
        """
        Resets the base timer
        """
        self.con.send_xid_command("e1")


    def query_base_timer(self):
        """
        gets the value from the device's base timer
        """
        (_, _, time) = unpack('<ccI', self.con.send_xid_command("e3", 6))
        return time


class ResponseDevice(BaseDevice):
    def __init__(self, connection,
                 name='Unknown XID Device',
                 keymap=None,
                 trigger_prefix="Button"):
        BaseDevice.__init__(self, connection, name)
        self.keymap = keymap
        self.trigger_name_prefix = trigger_prefix
        self.response_queue = []

    def poll_for_response(self):
        """
        Polls the device for user input

        If there is a keymapping for the device, the key map is applied
        to the key reported from the device.

        If a response is waiting to be processed, the response is appended
        to the internal response_queue
        """
        key_state = self.con.check_for_keypress()

        if key_state != NO_KEY_DETECTED:
            response = self.con.get_current_response()

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
                      is 0 on RB-series devices, and 2 on SV-1 voice key devices.
            time:     For the time being, this just returns 0.  There is
                      currently an issue with clock drift in the Cedrus XID
                      devices.  Once we have this issue resolved, time will
                      report the value of the RT timer in miliseconds.
        """
        response = self.response_queue[0]
        self.response_queue = self.response_queue[1:]
        return response


    def clear_response_queue(self):
        """
        Clears the response queue
        """
        self.response_queue = []


    def __str__(self):
        return '<ResponseDevice "%s">' % self.device_name


    def __repr__(self):
        return self.__str__()


class StimTracker(BaseDevice):
    """
    Class that encapsulates the StimTracker device.

    The pulse duration defaults to 100ms.  To change this, call
    StimTracker.set_pulse_duration(duration_in_miliseconds)
    """
    _lines = { 1: 1,
               2: 2,
               3: 4,
               4: 8,
               5: 16,
               6: 32,
               7: 64,
               8: 128}

    def __init__(self, connection, name="StimTracker"):
        BaseDevice.__init__(self, connection, name)
        self.con.set_using_stim_tracker(True)
        self.con.send_xid_command('a10')
        self.con.clear_digital_output_lines(0xff)
        self.set_pulse_duration(100)

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

    def activate_line(self, lines=None, bitmask=None,
                      leave_remaining_lines=False):
        """
        Triggers an output line on StimTracker.

        There are 8 output lines on StimTracker that can be raised in any
        combination.  To raise lines 1 and 7, for example, you pass in
        the list: activate_line(lines=[1, 7]).

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

        If you call activate_line(lines=4) with leave_remaining_lines=False (the
        default), if lines 1 and 8 were previously active, only line 4 will be
        active after the call.

        """
        if lines is None and bitmask is None:
            raise ValueError('Must set one of lines or bitmask')
        if lines is not None and bitmask is not None:
            raise ValueError('Can only set one of lines or bitmask')

        if bitmask is not None:
            if bitmask not in range(0, 256):
                raise ValueError('bitmask must be an integer between 0 and 255')

        if lines is not None:
            if not isinstance(lines, list):
                lines = [lines]

            bitmask = 0
            for l in lines:
                if l < 1 or l > 8:
                    raise ValueError('Line numbers must be between 1 and 8 '
                                     '(inclusive)')
                bitmask |= self._lines[l]

        self.con.set_digital_output_lines(bitmask, leave_remaining_lines)

    def clear_line(self, lines=None, bitmask=None,
                   leave_remaining_lines=False):
        """
        The inverse of activate_line.  If a line is active, it deactivates it.

        This has the same parameters as activate_line()
        """
        if lines is None and bitmask is None:
            raise ValueError('Must set one of lines or bitmask')
        if lines is not None and bitmask is not None:
            raise ValueError('Can only set one of lines or bitmask')

        if bitmask is not None:
            if bitmask not in range(0, 256):
                raise ValueError('bitmask must be an integer between 0 and 255')

        if lines is not None:
            if not isinstance(lines, list):
                lines = [lines]

            bitmask = 0
            for l in lines:
                if l < 1 or l > 8:
                    raise ValueError('Line numbers must be between 1 and 8 '
                                     '(inclusive)')
                bitmask |= self._lines[l]

        self.con.clear_digital_output_lines(bitmask, leave_remaining_lines)

    def __str__(self):
        return '<StimTracker "%s">' % self.device_name

    def __repr__(self):
        return self.__str__()


class XidError(Exception):
    pass

class XidDevice(object):
    """
    Class for interfacing with a Cedrus XID device.

    At the beginning of an experiment, the developer should call:

        XidDevice.reset_base_timer()

    Whenever a stimulus is presented, the developer should call:

        XidDevice.reset_rt_timer()

    Developers Note:  Currently there is a known issue of clock drift
    in the XID devices.  Due to this, the dict returned by
    XidDevice.get_next_response() returns 0 for the reaction time value.

    This issue will be resolved in a future release of this library.
    """
    def __init__(self, xid_connection):
        self.con = xid_connection
        self._impl = None
        self.init_device()


    def __del__(self):
        self.con.close()
        del self.con

    def is_stimtracker(self):
        return isinstance(self._impl, StimTracker)

    def is_response_device(self):
        return isinstance(self._impl, ResponseDevice)

    def init_device(self):
        """
        Initializes the device with the proper keymaps and name
        """
        try:
            product_id = int(self._send_command('_d2', 1))
        except ValueError:
            product_id = self._send_command('_d2', 1)

        if product_id == 0:
            self._impl = ResponseDevice(
                self.con,
                'Cedrus Lumina LP-400 Response Pad System',
                lumina_keymap)
        elif product_id == 1:
            self._impl = ResponseDevice(
                self.con,
                'Cedrus SV-1 Voice Key',
                None,
                'Voice Response')
        elif product_id == 2:
            model_id = int(self._send_command('_d3', 1))
            if model_id == 1:
                self._impl = ResponseDevice(
                    self.con,
                    'Cedrus RB-530',
                    rb_530_keymap)
            elif model_id == 2:
                self._impl = ResponseDevice(
                    self.con,
                    'Cedrus RB-730',
                    rb_730_keymap)
            elif model_id == 3:
                self._impl = ResponseDevice(
                    self.con,
                    'Cedrus RB-830',
                    rb_830_keymap)
            elif model_id == 4:
                self._impl = ResponseDevice(
                    self.con,
                    'Cedrus RB-834',
                    rb_834_keymap)
            else:
                raise XidError('Unknown RB Device')
        elif product_id == 'S':
            fw_major = int(self._send_command('_d4', 1))
            fw_minor = int(self._send_command('_d5', 1))

            if fw_major == 0 and fw_minor < 5:
                raise XidError('Invalid Firmware Version.  You must upgrade '
                               'your device to firmware release SC05. '
                               'Currently installed version: SC%d%d' % (
                                   fw_major, fw_minor))

            self._impl = StimTracker(
                self.con,
                'Cedrus StimTracker')

        elif product_id == -99:
            raise XidError('Invalid XID device')

    def _send_command(self, command, expected_bytes):
        """
        Send an XID command to the device
        """
        response = self.con.send_xid_command(command, expected_bytes)

        return response

    def __getattr__(self, attrname):
        return getattr(self._impl, attrname)

    def __str__(self):
        if self._impl is not None:
            return str(self._impl)
        else:
            return 'Uninitialized XID device'

    def __repr__(self):
        return self.__str__()

