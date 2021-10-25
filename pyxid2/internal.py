# -*- coding: utf-8 -*-
from struct import pack
from struct import unpack
import sys, time
from .constants import NO_KEY_DETECTED, FOUND_KEY_DOWN, FOUND_KEY_UP, \
     KEY_RELEASE_BITMASK, INVALID_PORT_BITS, XID_PACKET_SIZE, ST2_PACKET_SIZE

try:
    import ftd2xx
except OSError as e:
    if 'image not found' in str(e):
        raise OSError('ftd2xx drivers are not installed (or not in expected location)'
                      ' and these are required for the Cedrus pyxid2 library.\n'
                      '** Download from https://www.ftdichip.com/Drivers/D2XX.htm **')
    else:
        raise(e)  # not an error we know so pass it on



class XidConnection(object):
    def __init__(self, device, baud_rate=115200):
        self.ftd2xx_intermediate = device
        self.ftd2xx_con = 0
        self.baudrate = baud_rate
        self.__needs_interbyte_delay = True
        self.__packet_size = XID_PACKET_SIZE
        self.__response_buffer = b''
        self.__response_structs_queue = []
        # The set lines cmd on XID 1 response devices (RB-x30 series, Lumina LP-400 and SV-1)'ah'.
        # In all other cases (ST-1, XID2 devices) 'mh' is used instead.
        self.__using_stim_tracker = False
        self.__set_lines_cmd = 'ah'+chr(0)+chr(0)
        self.__line_state = 0

    def set_using_stim_tracker_output(self, using_st=True):
        if using_st:
            self.__using_stim_tracker = True
            self.__set_lines_cmd = 'mh'+chr(0)+chr(0)
            self.__needs_interbyte_delay = False
        else:
            self.__using_stim_tracker = False
            self.__set_lines_cmd = 'ah'+chr(0)+chr(0)
            self.__needs_interbyte_delay = True

    def set_resp_packet_size(self, st2_packet_size=True):
        if st2_packet_size:
            self.__packet_size = ST2_PACKET_SIZE # ST2 packets are larger

    def clear_digital_output_lines(self, lines, leave_remaining_lines=False):
        if lines not in list(range(0, 65536)):
            raise ValueError('lines must be between 0 and 65535')

        local_lines = ~lines
        if local_lines < 0:
            local_lines += 65536

        self.set_digital_output_lines(local_lines, leave_remaining_lines)

    def set_digital_output_lines(self, lines, leave_remaining_lines=False):
        if lines not in list(range(0, 65536)):
            raise ValueError('lines must be between 0 and 65535')

        if leave_remaining_lines:
            lines |= self.__line_state

        if self.__using_stim_tracker:
            self.__set_lines_cmd = 'mh'+chr(lines & 0x000000FF)+chr((lines >> 8) & 0x000000FF)
        else:
            lines_tmp = ~lines
            if lines_tmp < 0:
                lines_tmp += 65536
            self.__set_lines_cmd = 'ah'+chr(lines_tmp & 0x000000FF)+chr((lines >> 8) & 0x000000FF)

        self.write(self.__set_lines_cmd)
        self.__line_state = lines

    def set_digio_lines_to_mask(self, lines):
        command_char = b'm' if self.__using_stim_tracker else b'a'

        digio_cmd = pack('<ccH', command_char, b'h', lines)
        self.write_bytes(digio_cmd)

    def flush(self):
        self.ftd2xx_con.purge()

    def open(self):
        try:
            self.ftd2xx_con = ftd2xx.openEx(self.ftd2xx_intermediate)
        except ftd2xx.DeviceError:
            return False

        self.ftd2xx_con.setBaudRate(self.baudrate)
        self.ftd2xx_con.setDataCharacteristics(8, 0, 0)

        self.ftd2xx_con.setTimeouts(50, 50)
        self.ftd2xx_con.setUSBParameters(64,64)
        self.ftd2xx_con.setLatencyTimer(10)
        self.flush()

        return True

    def close(self):
        self.ftd2xx_con.close()

    def send_xid_command(self, command, bytes_expected=0):
        self.write(command)

        response = self.read(bytes_expected)

        return response

    def send_xid_byte_command(self, command, bytes_expected=0):
        self.write_bytes(command)

        response = self.read(bytes_expected)

        return response

    def read(self, bytes_to_read):
        return self.ftd2xx_con.read(bytes_to_read)

    def set_timeout(self, timeout):
        self.ftd2xx_con.setTimeouts(timeout, 50)

    def write(self, command):
        bytes_written = 0
        cmd_bytes = []

        self.ftd2xx_con.setTimeouts(50, 50)

        for i in command:
            if (sys.version_info >= (3, 0)):
                cmd_bytes += i.encode('latin1')
            else:
                cmd_bytes += i

        if self.__needs_interbyte_delay:
            for char in cmd_bytes:
                bytes_written += self.ftd2xx_con.write(bytes([char]))
                time.sleep(0.001)
        else:
            bytes_written = self.ftd2xx_con.write(bytes(cmd_bytes))

        return bytes_written

    def write_bytes(self, command):
        bytes_written = 0

        self.ftd2xx_con.setTimeouts(50, 50)

        if self.__needs_interbyte_delay:
            for char in command:
                bytes_written += self.ftd2xx_con.write(char)
                time.sleep(0.001)
        else:
            bytes_written = self.ftd2xx_con.write(command)

        return bytes_written

    def check_for_keypress(self):
        self.ftd2xx_con.setTimeouts(2, 50)
        response = self.read(self.__packet_size)

        response_found = NO_KEY_DETECTED
        if len(response) > 0:
            self.__response_buffer += response
            if self.__packet_size == 6:
                response_found = self.xid_input_found()
            else:
                response_found = self.st2_input_found()

        return response_found

    def xid_input_found(self):
        input_found = NO_KEY_DETECTED

        position_in_buf = 0

        while ((position_in_buf + self.__packet_size) <=
               len(self.__response_buffer)):

            exception_free = True

            try:
                (k, params, time) = unpack('<cBI',
                                           self.__response_buffer[
                                               position_in_buf:
                                               (position_in_buf +
                                                self.__packet_size)])
            except Exception as exc:
                exception_free = False
                print(('Failed to unpack serial bytes in xid_input_found. '
                      'Err: ' + str(exc)))

            if exception_free:
                """
                Refer to PROTOCOL AND TIMING COMMANDS section of
                https://cedrus.com/support/xid/commands.htm
                """
                if (k != b'k' or (params & INVALID_PORT_BITS) != 0):
                    self.__response_buffer = b''
                    self.flush()
                    print('Pyxid found unparseable bytes in the buffer. '
                          'Flushing buffer.')

                    break
                else:
                    response = {'port': 0,
                                'key': 0,
                                'pressed': False,
                                'time': 0}
                    response['port'] = params & 0x0F
                    response['key'] = ((params & 0xE0) >> 5)
                    response['pressed'] = (params & KEY_RELEASE_BITMASK) == \
                        KEY_RELEASE_BITMASK

                    if response['key'] == 0:
                        response['key'] = 8

                    response['time'] = time

                    if response['pressed']:
                        input_found = FOUND_KEY_DOWN
                    else:
                        input_found = FOUND_KEY_UP

                    self.__response_structs_queue += [response]

            position_in_buf += self.__packet_size

        self.__response_buffer = self.__response_buffer[position_in_buf:]

        return input_found

    def st2_input_found(self):
        input_found = NO_KEY_DETECTED

        position_in_buf = 0

        while ((position_in_buf + self.__packet_size) <=
               len(self.__response_buffer)):

            exception_free = True

            try:
                (o, port, key, pressed, time, null_byte) = unpack('<ccBcIB',
                                           self.__response_buffer[
                                               position_in_buf:
                                               (position_in_buf +
                                                self.__packet_size)])
            except Exception as exc:
                exception_free = False
                print(('Failed to unpack serial bytes in st2_input_found. '
                      'Err: ' + str(exc)))

            if exception_free:
                """
                Refer to PROTOCOL AND TIMING COMMANDS section of
                https://cedrus.com/support/xid/commands.htm
                """
                if (o != b'o' or null_byte != 0):
                    self.__response_buffer = b''
                    self.flush()
                    print('Pyxid found unparseable bytes in the buffer. '
                          'Flushing buffer.')

                    break
                else:
                    response = {'port': 0,
                                'key': 0,
                                'pressed': False,
                                'time': 0}
                    response['port'] = port
                    response['key'] = key
                    response['pressed'] = True if pressed == b'1' else False

                    if response['key'] == 0:
                        response['key'] = 8

                    response['time'] = time

                    if response['pressed']:
                        input_found = FOUND_KEY_DOWN
                    else:
                        input_found = FOUND_KEY_UP

                    self.__response_structs_queue += [response]

            position_in_buf += self.__packet_size

        self.__response_buffer = self.__response_buffer[position_in_buf:]

        return input_found

    def get_current_response(self):
        """
        reads the current response data from the object and returns
        it in a dict.

        Currently 'time' is reported as 0 until clock drift issues are
        resolved.
        """
        response = {'port': 0,
                    'pressed': False,
                    'key': 0,
                    'time': 0}
        if len(self.__response_structs_queue) > 0:
            # make a copy just in case any other internal members of
            # XidConnection were tracking the structure
            response = self.__response_structs_queue[0].copy()
            # we will now hand over 'response' to the calling code,
            # so remove it from the internal queue
            self.__response_structs_queue.pop(0)

        return response
