# -*- coding: utf-8 -*-
from struct import unpack
import sys, time
from .constants import NO_KEY_DETECTED, FOUND_KEY_DOWN, FOUND_KEY_UP, \
     KEY_RELEASE_BITMASK, INVALID_PORT_BITS

import ftd2xx

class XidConnection(object):
    def __init__(self, device, baud_rate=115200):
        self.ftd2xx_intermediate = device
        self.ftd2xx_con = 0
        self.baudrate = baud_rate
        self.__needs_interbyte_delay = True
        self.__xid_packet_size = 6
        self.__response_buffer = b''
        self.__response_structs_queue = []
        # The set lines cmd on XID 1 response devices (RB-x30 series, Lumina LP-400 and SV-1)'ah'.
        # In all other cases (ST-1, XID2 devices) 'mh' is used instead.
        self.__using_stim_tracker = False
        self.__set_lines_cmd = 'ah'+chr(0)+chr(0)
        self.__line_state = 0

    def set_using_stim_tracker(self, using_st=True):
        if using_st:
            self.__using_stim_tracker = True
            self.__set_lines_cmd = 'mh'+chr(0)+chr(0)
            self.__needs_interbyte_delay = False
        else:
            self.__using_stim_tracker = False
            self.__set_lines_cmd = 'ah'+chr(0)+chr(0)
            self.__needs_interbyte_delay = True

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

    def flush(self):
        self.ftd2xx_con.purge()

    def open(self):
        self.ftd2xx_con = ftd2xx.openEx(self.ftd2xx_intermediate)

        self.ftd2xx_con.setBaudRate(self.baudrate)
        self.ftd2xx_con.setDataCharacteristics(8, 0, 0)

        self.ftd2xx_con.setTimeouts(50, 50)
        self.ftd2xx_con.setUSBParameters(64,64)
        self.ftd2xx_con.setLatencyTimer(10)
        self.flush()

    def close(self):
        self.ftd2xx_con.close()

    def send_xid_command(self, command, bytes_expected=0):
        self.write(command)

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

    def check_for_keypress(self):
        self.ftd2xx_con.setTimeouts(2, 50)
        response = self.read(self.__xid_packet_size)

        response_found = NO_KEY_DETECTED
        if len(response) > 0:
            self.__response_buffer += response
            response_found = self.xid_input_found()

        return response_found

    def xid_input_found(self):
        input_found = NO_KEY_DETECTED

        position_in_buf = 0

        while ((position_in_buf + self.__xid_packet_size) <=
               len(self.__response_buffer)):

            exception_free = True

            try:
                (k, params, time) = unpack('<cBI',
                                           self.__response_buffer[
                                               position_in_buf:
                                               (position_in_buf +
                                                self.__xid_packet_size)])
            except Exception as exc:
                exception_free = False
                print(('Failed to unpack serial bytes in xid_input_found. '
                      'Err: ' + str(exc)))

            if exception_free:

                """
                Try to determine if we have a valid packet.  Our options
                are limited; here is what we look for:

                a.  The first byte must be the letter 'k'

                b.	Bits 0-3 of the second byte indicate the port number.
                Lumina and RB-x30 models use only bits 0 and 1; SV-1 uses
                only bits 1 and 2.  We check that the two remaining bits are
                zero.

                Refer to: http://www.cedrus.com/xid/protocols.htm
                """
                if (k != b'k' or (params & INVALID_PORT_BITS) != 0):
                    self.__response_buffer = b''
                    self.flush()
                    print('Pyxid found unparseable bytes in the buffer. '
                          'Flushing buffer.')

                    break
                else:
                    response = {'port': 0,
                                'pressed': False,
                                'key': 0,
                                'time': 0}
                    response['port'] = params & 0x0F
                    response['pressed'] = (params & KEY_RELEASE_BITMASK) == \
                        KEY_RELEASE_BITMASK
                    response['key'] = ((params & 0xE0) >> 5)

                    if response['key'] == 0:
                        response['key'] = 8

                    response['time'] = time

                    if response['pressed']:
                        input_found = FOUND_KEY_DOWN
                    else:
                        input_found = FOUND_KEY_UP

                    self.__response_structs_queue += [response]

            # Note: if an exception was caught, then we essentially
            # THROW AWAY the bytes equal to one packet size.  Is there
            # anything else we could do?
            position_in_buf += self.__xid_packet_size

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
