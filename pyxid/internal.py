# -*- coding: utf-8 -*-
from struct import unpack
import time
from constants import NO_KEY_DETECTED, FOUND_KEY_DOWN, FOUND_KEY_UP, \
     KEY_RELEASE_BITMASK, INVALID_PORT_BITS

class XidConnection(object):
    def __init__(self, serial_port, baud_rate=115200):
        self.serial_port = serial_port
        self.serial_port.baudrate = baud_rate
        self.__needs_interbyte_delay = True
        self.__xid_packet_size = 6
        self.__default_read_timeout = 0
        self.__bytes_in_buffer = 0
        self.__response_buffer = ''
        self.__last_resp_pressed = False
        self.__last_resp_port = 0
        self.__last_resp_key = 0
        self.__last_resp_rt = 0
        self.__first_valid_packet = -1


    def flush_input(self):
        self.serial_port.flushInput()


    def flush_output(self):
        self.serial_port.flushOutput()


    def open(self):
        self.serial_port.open()
        self.flush_input()
        self.flush_output()


    def close(self):
        self.serial_port.close()


    def send_xid_command(self, command, bytes_expected=0,timeout=0.1):
        self.write(command)

        self.serial_port.timeout = timeout
        response = self.read(bytes_expected)
        self.serial_port.timeout = self.__default_read_timeout

        return response


    def read(self, bytes_to_read):
        return self.serial_port.read(bytes_to_read)



    def write(self, command):
        bytes_written = 0
        if self.__needs_interbyte_delay:
            for char in command:
                bytes_written += self.serial_port.write(char)
                time.sleep(0.001)
        else:
            bytes_written = self.serial_port.write(command)

        return bytes_written


    def check_for_keypress(self):
        response = self.read(6)

        response_found = NO_KEY_DETECTED
        if len(response) > 0:
            self.__bytes_in_buffer += len(response)
            self.__response_buffer += response
            response_found = self.xid_input_found()

        return response_found

    def xid_input_found(self):
        input_found = NO_KEY_DETECTED

        if self.__bytes_in_buffer >= 6:
            last_byte_index = self.__bytes_in_buffer - self.__xid_packet_size

            i = 0
            while i <= last_byte_index:
                try:
                    (k, params, time) = unpack('<cBI',
                                               self.__response_buffer[
                                                   last_byte_index:
                                                   last_byte_index+6])
                except Exception:
                    i += 1
                    continue

                if (k == 'k' and
                    (params & INVALID_PORT_BITS) == 0 and
                    self.__response_buffer[i+5] == '\x00'):

                    # found a valid XID packet
                    self.__first_valid_packet = i

                    self.__last_resp_pressed = (
                        params & KEY_RELEASE_BITMASK) == KEY_RELEASE_BITMASK
                    self.__last_resp_port = params & 0x0F;
                    key = ((params & 0xE0) >> 5)
                    if key == 0:
                        key = 8

                    self.__last_resp_key = key

                    self.__last_resp_rt = time

                    if self.__last_resp_pressed:
                        input_found = FOUND_KEY_DOWN
                    else:
                        input_found = FOUND_KEY_UP

                i += 1

        return input_found


    def get_current_response(self):
        """
        reads the current response data from the object and returns
        it in a dict.

        Currently 'time' is reported as 0 until clock drift issues are
        resolved.
        """
        response = {'time': 0, #self.__last_resp_rt,
                    'pressed': self.__last_resp_pressed,
                    'key': self.__last_resp_key,
                    'port': self.__last_resp_port}

        self.remove_current_response()
        return response


    def remove_current_response(self):
        if self.__first_valid_packet != -1:
            self.__response_buffer = self.__response_buffer[
                self.__first_valid_packet + self.__xid_packet_size:]
            self.__bytes_in_buffer -= self.__xid_packet_size
            self.__first_valid_packet = -1


