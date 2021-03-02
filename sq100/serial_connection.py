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

from __future__ import annotations

import logging
import serial
from dataclasses import dataclass

from typing import Any, cast, Optional

from sq100.exceptions import SQ100SerialException

logger = logging.getLogger(__name__)


@dataclass
class SerialConfig:
    port: str
    baudrate: int
    timeout: float


class SerialConnection:
    connection: Optional[serial.Serial] = None

    def __init__(self, config: SerialConfig):
        self.config = config

    def __enter__(self) -> SerialConnection:
        try:
            self.connection = serial.Serial(
                baudrate=self.config.baudrate,
                port=self.config.port,
                timeout=self.config.timeout)
            logger.debug("serial connection established on %s",
                         self.connection.portstr)
            return self
        except serial.SerialException:
            logger.critical("error establishing serial connection")
            raise SQ100SerialException

    def __exit__(self, *_: Any) -> None:
        """disconnect the serial connection"""
        assert self.connection is not None
        self.connection.close()
        logger.debug("serial connection closed")

    def write(self, command: bytes) -> None:
        assert self.connection is not None
        logger.debug("writing data: %s", command)
        try:
            self.connection.write(command)
        except serial.SerialTimeoutException:
            logger.critical("write timeout occured")
            raise SQ100SerialException

    def read(self, size: int) -> bytes:
        assert self.connection is not None
        data = self.connection.read(size)
        logger.debug("reading data:: %s", data)
        return cast(bytes, data)
