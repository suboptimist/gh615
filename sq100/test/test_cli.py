# SQ100 - Serial Communication with the a-rival SQ100 heart rate computer
# Copyright (C) 2021  Timo Nachstedt
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

from sq100 import cli
from sq100 import serial_connection

default_serial_config = serial_connection.SerialConfig(
    port="my_port", baudrate=42, timeout=1.23
)


def test_parse_args__exits_if_no_argument_give() -> None:
    with pytest.raises(SystemExit):
        cli.parse_args(args=[], default_serial_config=default_serial_config)


def test_parse_args__list_with_no_args_returns_serial_defaults() -> None:
    opts = cli.parse_args(args=["list"], default_serial_config=default_serial_config)
    assert isinstance(opts, cli.ListOptions)
    assert opts.serial_config == default_serial_config


def test_parse_args__list_allows_configuring_serial_config() -> None:
    opts = cli.parse_args(
        args=[
            "list",
            "--comport",
            "your_port",
            "--baudrate",
            "43",
            "--timeout",
            "2.34",
        ],
        default_serial_config=default_serial_config,
    )
    assert isinstance(opts, cli.ListOptions)
    assert opts.serial_config.port == "your_port"
    assert opts.serial_config.baudrate == 43
    assert opts.serial_config.timeout == 2.34


def test_parse_args__download_with_no_args_returns_serial_defaults() -> None:
    opts = cli.parse_args(
        args=["download"], default_serial_config=default_serial_config
    )
    assert isinstance(opts, cli.DownloadOptions)
    assert opts.serial_config == default_serial_config


def test_parse_args__download_allows_configuring_serial_config() -> None:
    opts = cli.parse_args(
        args=[
            "download",
            "--comport",
            "your_port",
            "--baudrate",
            "43",
            "--timeout",
            "2.34",
        ],
        default_serial_config=default_serial_config,
    )
    assert isinstance(opts, cli.DownloadOptions)
    assert opts.serial_config.port == "your_port"
    assert opts.serial_config.baudrate == 43
    assert opts.serial_config.timeout == 2.34


def test_parse_args__download_understands_single_track_id() -> None:
    opts = cli.parse_args(
        args=["download", "2"],
        default_serial_config=default_serial_config,
    )
    assert isinstance(opts, cli.DownloadOptions)
    assert opts.track_id == [2]


def test_parse_args__download_understands_complex_track_id_list() -> None:
    opts = cli.parse_args(
        args=["download", "2,5-7,8,13"],
        default_serial_config=default_serial_config,
    )
    assert isinstance(opts, cli.DownloadOptions)
    assert opts.track_id == [2, 5, 6, 7, 8, 13]


def test_parse_args__download_sets_merge_to_false_by_default() -> None:
    opts = cli.parse_args(
        args=["download"],
        default_serial_config=default_serial_config,
    )
    assert isinstance(opts, cli.DownloadOptions)
    assert opts.merge is False


def test_parse_args__download_sets_merge_to_true_if_flag_is_given() -> None:
    opts = cli.parse_args(
        args=["download", "--merge"],
        default_serial_config=default_serial_config,
    )
    assert isinstance(opts, cli.DownloadOptions)
    assert opts.merge is True


def test_parse_args__download_sets_latest_to_false_by_default() -> None:
    opts = cli.parse_args(
        args=["download"],
        default_serial_config=default_serial_config,
    )
    assert isinstance(opts, cli.DownloadOptions)
    assert opts.latest is False


def test_parse_args__download_sets_latest_to_true_if_flag_is_given() -> None:
    opts = cli.parse_args(
        args=["download", "--latest"],
        default_serial_config=default_serial_config,
    )
    assert isinstance(opts, cli.DownloadOptions)
    assert opts.latest is True