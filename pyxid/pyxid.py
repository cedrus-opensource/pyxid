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
        self.device_name = 'Unknown XID Device'
        self.trigger_name_prefix = 'Button'
        self.response_queue = []
        self.keymap = None

        self.init_device()


    def __del__(self):
        self.con.close()
        del self.con


    def init_device(self):
        """
        Initializes the device with the proper keymaps and name
        """
        product_id = int(self.get_xid_inquiry('_d2',1))

        if product_id == 0:
            self.device_name = 'Cedrus Lumina LP-400 Response Pad System'
            self.keymap = lumina_keymap
        elif product_id == 1:
            self.device_name = 'Cedrus SV-1 Voice Key'
            self.trigger_name_prefix = 'Voice Response'
        elif product_id == 2:
            model_id = int(self.get_xid_inquiry('_d3',1))
            if model_id == 1:
                self.device_name = 'Cedrus RB-530'
                self.keymap = rb_530_keymap
            elif model_id == 2:
                self.device_name = 'Cedrus RB-730'
                self.keymap = rb_730_keymap
            elif model_id == 3:
                self.device_name = 'Cedrus RB-830'
                self.keymap = rb_830_keymap
            elif model_id == 4:
                self.device_name = 'Cedrus RB-830'
                self.keymap = rb_834_keymap
            else:
                self.device_name = 'Unknown Cedrus RB-Series Device'
        elif product_id == -99:
            self.device_name = 'Invalid XID Device'



    def get_xid_inquiry(self, command, expected_bytes, timeout=0.1):
        """
        Send an XID command to the device
        """
        response = self.con.send_xid_command(command, expected_bytes)

        return response


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
        (c1, c2, time) = unpack('<ccI',self.con.send_xid_command("e3",6))
        return time


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
        return '<XidDevice "%s">' % self.device_name


    def __repr__(self):
        return self.__str__()

