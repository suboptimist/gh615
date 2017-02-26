import logging
import serial

from sq100.exceptions import SQ100SerialException


logger = logging.getLogger(__name__)


class SerialConnection():
    _sleep = 2

    def __init__(self, baudrate=None, port=None, timeout=None):
        self.serial = serial.Serial()
        if baudrate is not None:
            self.baudrate = baudrate
        if port is not None:
            self.port = port
        if timeout is not None:
            self.timeout = timeout

    @property
    def baudrate(self):
        return self.serial.baudrate

    @baudrate.setter
    def baudrate(self, b):
        logger.debug("setting baudrate to %s", b)
        self.serial.baudrate = b

    @property
    def port(self):
        return self.serial.port

    @port.setter
    def port(self, p):
        logger.debug("setting port to %s", p)
        self.serial.port = p

    @property
    def timeout(self):
        return self.serial.timeout

    @timeout.setter
    def timeout(self, t):
        logger.debug("setting port to %s", t)
        self.serial.timeout = t

    def connect(self):
        try:
            self.serial.open()
            logger.debug("serial connection on %s", self.serial.portstr)
        except serial.SerialException:
            logger.critical("error establishing serial connection")
            raise SQ100SerialException

    def disconnect(self):
        """disconnect the serial connection"""
        self.serial.close()
        logger.debug("serial connection closed")

    def write(self, command):
        logger.debug("writing data: %s", command)
        try:
            self.serial.write(command)
        except serial.SerialTimeoutException:
            logger.critical("write timeout occured")
            raise SQ100SerialException

    def read(self, size=2070):
        data = self.serial.read(size)
        logger.debug("reading data:: %s", data)
        return data

    def query(self, command):
        for attempt in range(3):
            self.write(command)
            data = self.read()
            if data:
                return data
            logger.debug("no data at serial port at attempt %d", attempt)
        raise SQ100SerialException("query failed")

#     def _diagnostic(self):
#         """check if a connection can be established"""
#         try:
#             self._connectSerial()
#             self._querySerial('whoAmI')
#             self._disconnectSerial()
#             self.logger.info("serial connection established successfully")
#             return True
#         except SQ100SerialException:
#             self.logger.info("error establishing serial port connection, "
#                              "please check your config.ini file")
#             return False
