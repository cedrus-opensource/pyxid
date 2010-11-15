# -*- coding: utf-8 -*-
from serial import serial_for_url, Serial
from serial.serialutil import SerialException
import os, sys

class SerialPort(object):
    def __init__(self, serial_port, baud_rate=115200):
        if sys.platform == 'darwin':
            self.impl = MacSerialPort(serial_port, baud_rate)
        elif sys.platform == 'linux2':
            self.impl = LinuxSerialPort(serial_port, baud_rate)
        else:
            self.impl = GenericSerialPort(serial_port, baud_rate)

    def __getattr__(self, attr):
        return getattr(self.impl, attr)


    @staticmethod
    def available_ports():
        if sys.platform == 'darwin':
            return MacSerialPort.available_ports()
        elif sys.platform == 'linux2':
            return LinuxSerialPort.available_ports()
        else:
            return GenericSerialPort.available_ports()


class LinuxSerialPort(object):
    """
    USB-serial devices on Linux show up as /dev/ttyUSB?

    pySerial expects /dev/tty? (no USB).
    """
    def __init__(self, serial_port, baud_rate=115200):
        self.serial_port = serial_port
        self.serial_port.setBaudrate(baud_rate)


    def __getattr__(self, attr):
        return getattr(self.serial_port, attr)


    @staticmethod
    def available_ports():
        usb_serial_ports = filter(
            (lambda x: x.startswith('ttyUSB')),
            os.listdir('/dev'))

        ports = []
        for p in usb_serial_ports:
            ports.append(serial_for_url('/dev/'+p, do_not_open=True))

        return ports


class GenericSerialPort(object):
    def __init__(self, serial_port, baud_rate=115200):
        self.serial_port = serial_port
        self.serail_port.setBaudrate(baud_rate)

    @staticmethod
    def available_ports():
        """
        Scans COM1 through COM255 for available serial ports

        returns a list of available ports
        """
        ports = []

        for i in range(256):
            try:
                p = Serial(i)
                p.close()
                ports.append(p)
            except SerialException:
                pass

        return ports


    def __getattr__(self, attr):
        """
        forward calls to the internal serial.Serial instance
        """
        return getattr(self.serial_port, attr)


class MacSerialPort(object):
    """
    USB-Serial ports on Mac OS show up as /dev/cu.usbserial-*

    pySerial expects them to be /dev/cuad*
    """
    def __init__(self, serial_port, baud_rate=115200):
        self.serial_port = serial_port
        self.serial_port.setBaudrate(baud_rate)

    @staticmethod
    def available_ports():
        usb_serial_ports = filter(
            (lambda x : x.startswith('cu.usbserial')),
            os.listdir('/dev'))

        ports = []
        for p in usb_serial_ports:
            ports.append(serial_for_url('/dev/'+p, do_not_open=True))

        return ports


    def __getattr__(self, attr):
        """
        forward calls to the internal serial.Serial instance
        """
        return getattr(self.serial_port, attr)


