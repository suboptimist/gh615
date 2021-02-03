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

import pytest
from pytest_mock import MockerFixture
import serial

from sq100.serial_connection import SerialConnection, SerialConfig
from sq100.exceptions import SQ100SerialException


def test_enter__everything_fine_if_successful(mocker: MockerFixture) -> None:
    mock_serial = mocker.patch("serial.Serial")
    serial_instance = mock_serial.return_value
    config = SerialConfig(port="port", baudrate=10, timeout=11.11)
    with SerialConnection(config) as connection:
        assert connection.serial == serial_instance
    serial_instance.open.assert_called_once_with()


def test_enter__raises_for_serial_exception(mocker: MockerFixture) -> None:
    mock_serial = mocker.patch("serial.Serial")
    serial_instance = mock_serial.return_value
    serial_instance.open.side_effect = serial.SerialException
    config = SerialConfig(port="port", baudrate=10, timeout=11.11)
    with pytest.raises(SQ100SerialException):
        with SerialConnection(config):
            pass


def test_exit__closes_connection(mocker: MockerFixture) -> None:
    mock_serial = mocker.patch("serial.Serial")
    serial_instance = mock_serial.return_value
    config = SerialConfig(port="port", baudrate=10, timeout=11.11)
    with SerialConnection(config):
        pass
    serial_instance.close.assert_called_once_with()


def test_write__forwards_call_to_serial(mocker: MockerFixture) -> None:
    mock_serial = mocker.patch("serial.Serial")
    serial_instance = mock_serial.return_value
    config = SerialConfig(port="port", baudrate=10, timeout=11.11)
    connection = SerialConnection(config)
    connection.write(b'\x00\x80')
    serial_instance.write.assert_called_once_with(b'\x00\x80')


def test_write__raises_if_forwarding_failes(mocker: MockerFixture) -> None:
    mock_serial = mocker.patch("serial.Serial")
    serial_instance = mock_serial.return_value
    serial_instance.write.side_effect = serial.SerialTimeoutException
    config = SerialConfig(port="port", baudrate=10, timeout=11.11)
    connection = SerialConnection(config)
    with pytest.raises(SQ100SerialException):
        connection.write(b'\x00\x80')
    serial_instance.write.assert_called_once_with(b'\x00\x80')


def test_read__forwards_data_from_serial(mocker: MockerFixture) -> None:
    mock_serial = mocker.patch("serial.Serial")
    serial_instance = mock_serial.return_value
    serial_instance.read.return_value = b'\xaa\xbb\xcc'
    config = SerialConfig(port="port", baudrate=10, timeout=11.11)
    connection = SerialConnection(config)
    assert connection.read(1234) == b'\xaa\xbb\xcc'
