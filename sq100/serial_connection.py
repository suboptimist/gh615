# SQ100 - Serial Communication with the a-rival SQ100 heart rate computer
# Copyright (C) 2017  Timo Nachstedt
#
# This file is part of SQ100.
#
# SQ100 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SQ100 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import serial

from sq100.exceptions import SQ100SerialException
from typing import cast, Optional

logger = logging.getLogger(__name__)


class SerialConnection():
    _sleep = 2

    def __init__(
            self,
            baudrate: int = None,
            port: str = None,
            timeout: float = None):
        self.serial = serial.Serial()
        if baudrate is not None:
            self.baudrate = baudrate
        if port is not None:
            self.port = port
        if timeout is not None:
            self.timeout = timeout

    @property
    def baudrate(self) -> int:
        return cast(int, self.serial.baudrate)

    @baudrate.setter
    def baudrate(self, b: int) -> None:
        logger.debug("setting baudrate to %s", b)
        self.serial.baudrate = b

    @property
    def port(self) -> str:
        return cast(str, self.serial.port)

    @port.setter
    def port(self, p: str) -> None:
        logger.debug("setting port to %s", p)
        self.serial.port = p

    @property
    def timeout(self) -> Optional[float]:
        return cast(Optional[float], self.serial.timeout)

    @timeout.setter
    def timeout(self, t: float) -> None:
        logger.debug("setting port to %s", t)
        self.serial.timeout = t

    def connect(self) -> None:
        try:
            self.serial.open()
            logger.debug("serial connection on %s", self.serial.portstr)
        except serial.SerialException:
            logger.critical("error establishing serial connection")
            raise SQ100SerialException

    def disconnect(self) -> None:
        """disconnect the serial connection"""
        self.serial.close()
        logger.debug("serial connection closed")

    def write(self, command: bytes) -> None:
        logger.debug("writing data: %s", command)
        try:
            self.serial.write(command)
        except serial.SerialTimeoutException:
            logger.critical("write timeout occured")
            raise SQ100SerialException

    def read(self, size: int = 3000) -> bytes:
        data = self.serial.read(size)
        logger.debug("reading data:: %s", data)
        return cast(bytes, data)

    def query(self, command: bytes) -> Optional[bytes]:
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
