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


import datetime
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from sq100 import cli, serial_connection
from sq100.test import dummies, test_arival_sq100

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


def test_parse_args__exits_for_wrong_command() -> None:
    with pytest.raises(SystemExit):
        cli.parse_args(
            args=["foo"],
            default_serial_config=default_serial_config,
        )


def test_show_tracklist__shows_table_of_tracks(
    capsys: pytest.CaptureFixture[str], mocker: MockerFixture
) -> None:
    mocked_get_track_list = mocker.patch("sq100.arival_sq100.get_track_list")
    mocked_get_track_list.return_value = [
        test_arival_sq100.make_track_list_entry(
            date=datetime.datetime(2001, 2, 3, 4, 5, 6),
            distance=42,
            duration=datetime.timedelta(hours=1, minutes=2, seconds=3),
            no_track_points=11,
            no_laps=12,
            memory_block_index=13,
        )
    ]
    cli.show_tracklist(default_serial_config)
    captured = capsys.readouterr()
    expected = (
        "  id  date                   distance  duration      trkpnts    laps    mem. index"  # noqa: E501
        "----  -------------------  ----------  ----------  ---------  ------  ------------"  # noqa: E501
        "   0  2001-02-03 04:05:06          42  1:02:03            11      12            13"  # noqa: E501
    )
    assert captured.out == expected


def test_show_tracklist__shows_no_tracks_found_if_no_tracks_are_returned(
    capsys: pytest.CaptureFixture[str], mocker: MockerFixture
) -> None:
    mocked_get_track_list = mocker.patch("sq100.arival_sq100.get_track_list")
    mocked_get_track_list.return_value = []
    cli.show_tracklist(default_serial_config)
    captured = capsys.readouterr()
    assert captured.out == "no tracks found\n"


def test_download_tracks__creates_gpx_files(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    mocked_get_tracks = mocker.patch("sq100.arival_sq100.get_tracks")
    mocked_get_tracks.return_value = [
        dummies.make_track(info=dummies.make_track_info(id=1)),
        dummies.make_track(info=dummies.make_track_info(id=3)),
    ]
    cli.download_tracks(
        serial_config=default_serial_config, track_ids=[1, 3], output_dir=tmp_path
    )
    assert (tmp_path / "downloaded_tracks-1.gpx").is_file()
    assert (tmp_path / "downloaded_tracks-3.gpx").is_file()


def test_download_tracks__just_returns_if_track_is_list_is_empty(
    tmp_path: Path,
) -> None:
    cli.download_tracks(
        serial_config=default_serial_config, track_ids=[], output_dir=tmp_path
    )


def test_download_tracks__adds_latest_track_id_if_flag_is_given(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    mocked_get_track_list = mocker.patch("sq100.arival_sq100.get_track_list")
    mocked_get_track_list.return_value = [test_arival_sq100.make_track_list_entry(id=8)]
    mocked_get_tracks = mocker.patch("sq100.arival_sq100.get_tracks")
    mocked_get_tracks.return_value = []
    cli.download_tracks(
        serial_config=default_serial_config,
        track_ids=[1, 3],
        latest=True,
        output_dir=tmp_path,
    )
    mocked_get_tracks.assert_called_once_with(
        config=default_serial_config, track_ids=[1, 3, 8]
    )


def test_download_tracks__creates_single_gpx_file_if_merge_is_true(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    mocked_get_tracks = mocker.patch("sq100.arival_sq100.get_tracks")
    mocked_get_tracks.return_value = [
        dummies.make_track(info=dummies.make_track_info(id=1)),
        dummies.make_track(info=dummies.make_track_info(id=3)),
    ]
    cli.download_tracks(
        serial_config=default_serial_config,
        track_ids=[1, 3],
        merge=True,
        output_dir=tmp_path,
    )
    assert (tmp_path / "downloaded_tracks.gpx").is_file()


def test_get_latest_track_id__returns_id_of_most_recent_date(
    mocker: MockerFixture,
) -> None:
    mocked_get_track_list = mocker.patch("sq100.arival_sq100.get_track_list")
    mocked_get_track_list.return_value = [
        test_arival_sq100.make_track_list_entry(
            date=datetime.datetime(2001, 2, 3, 4, 5, 6), id=10
        ),
        test_arival_sq100.make_track_list_entry(
            date=datetime.datetime(2002, 2, 3, 4, 5, 6), id=11
        ),
        test_arival_sq100.make_track_list_entry(
            date=datetime.datetime(2001, 12, 3, 4, 5, 6), id=12
        ),
    ]
    latest_track_id = cli.get_latest_track_id(default_serial_config)
    assert latest_track_id == 11


def test_get_latest_track_id__returns_none_if_track_list_is_empty(
    mocker: MockerFixture,
) -> None:
    mocked_get_track_list = mocker.patch("sq100.arival_sq100.get_track_list")
    mocked_get_track_list.return_value = []
    latest_track_id = cli.get_latest_track_id(default_serial_config)
    assert latest_track_id is None
