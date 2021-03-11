# SQ100 - Serial Communication with the a-rival SQ100 heart rate computer
# Copyright (C) 2017-2021  Timo Nachstedt
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


import argparse
import configparser
import logging
import os
import sys
import tabulate

from dataclasses import dataclass
from typing import Literal, List, Optional, Set, Union

from sq100 import serial_connection
from sq100 import arival_sq100
from sq100 import gpx

logging.basicConfig(filename="sq100.log", level=logging.DEBUG)


@dataclass
class ListOptions:
    serial_config: serial_connection.SerialConfig


@dataclass
class DownloadOptions:
    serial_config: serial_connection.SerialConfig
    track_id: List[int]
    merge: bool
    latest: bool


Options = Union[ListOptions, DownloadOptions]


def main() -> None:
    default_serial_config = load_default_serial_config()
    options = parse_args(args=sys.argv, default_serial_config=default_serial_config)
    if isinstance(options, ListOptions):
        show_tracklist(serial_config=options.serial_config)
    elif isinstance(options, DownloadOptions):
        download_tracks(
            serial_config=options.serial_config,
            track_ids=options.track_id,
            merge=options.merge,
            latest=options.latest,
        )


def load_default_serial_config() -> serial_connection.SerialConfig:
    config = configparser.ConfigParser()
    config.read(["sq100.cfg", os.path.expanduser("~/.sq100.cfg")])
    return serial_connection.SerialConfig(
        port=config["serial"].get("comport", fallback="/dev/ttyUSB0"),
        baudrate=config["serial"].getint("baudrate", fallback=115200),
        timeout=config["serial"].getfloat("timeout", fallback=5.0),
    )


def parse_args(
    args: List[str], default_serial_config: serial_connection.SerialConfig
) -> Options:
    serial_config_parser = argparse.ArgumentParser(
        add_help=False, formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    serial_config_parser.add_argument(
        "-c",
        "--comport",
        help="comport for serial communication",
        default=default_serial_config.port,
    )
    serial_config_parser.add_argument(
        "-b",
        "--baudrate",
        help="baudrate for serial communication",
        type=int,
        default=default_serial_config.baudrate,
    )
    serial_config_parser.add_argument(
        "-t",
        "--timeout",
        help="timeout for serial communication",
        type=float,
        default=default_serial_config.timeout,
    )

    parser = argparse.ArgumentParser(
        description="Serial Communication with the Arival SQ100 heart rate computer"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "list",
        parents=[serial_config_parser],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser_download = subparsers.add_parser(
        name="download",
        parents=[serial_config_parser],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser_download.add_argument(
        "track_ids",
        help="list of track ids to download",
        type=parse_range,
        nargs="?",
        default=[],
    )
    parser_download.add_argument(
        "-f", "--format", help="the format to export to", choices=["gpx"]
    )
    parser_download.add_argument(
        "-m", "--merge", help="merge into single file?", action="store_true"
    )
    parser_download.add_argument(
        "-l", "--latest", help="download latest track", action="store_true"
    )

    opts = parser.parse_args(args=args)

    if opts.command == "list":
        return ListOptions(
            serial_config=serial_connection.SerialConfig(
                port=opts.comport, baudrate=opts.baudrate, timeout=opts.timeout
            ),
        )
    if opts.command == "download":
        return DownloadOptions(
            serial_config=serial_connection.SerialConfig(
                port=opts.comport, baudrate=opts.baudrate, timeout=opts.timeout
            ),
            track_id=opts.track_ids,
            merge=opts.merge,
            latest=opts.latest,
        )
    raise ValueError("Unknown command")


def parse_range(astr: str) -> List[int]:
    result: Set[int] = set()
    for part in astr.split(","):
        x = part.split("-")
        result.update(range(int(x[0]), int(x[-1]) + 1))
    return sorted(result)


def show_tracklist(serial_config: serial_connection.SerialConfig) -> None:
    tracks = arival_sq100.get_track_list(serial_config)
    if tracks:
        table = [
            [
                track.id,
                track.date,
                track.distance,
                track.duration,
                track.no_track_points,
                track.no_laps,
                track.memory_block_index,
            ]
            for track in tracks
        ]
        headers = [
            "id",
            "date",
            "distance",
            "duration",
            "trkpnts",
            "laps",
            "mem. index",
        ]
        print(tabulate.tabulate(table, headers=headers))
    else:
        print("no tracks found")


def download_tracks(
    serial_config: serial_connection.SerialConfig,
    track_ids: List[int] = [],
    merge: bool = False,
    latest: bool = False,
) -> None:
    if latest:
        latest_track_id = get_latest_track_id(serial_config=serial_config)
        if latest_track_id is not None:
            track_ids.append(latest_track_id)
    if len(track_ids) == 0:
        return
    tracks = arival_sq100.get_tracks(config=serial_config, track_ids=track_ids)
    if merge:
        gpx.store_tracks_to_file(
            tracks=arival_sq100.tracks_to_gpx(tracks), filename="downloaded_tracks.gpx"
        )
    else:
        for track in tracks:
            gpx.store_tracks_to_file(
                tracks=[arival_sq100.track_to_gpx(track)],
                filename="downloaded_tracks-%s.gpx" % track.info.id,
            )


def get_latest_track_id(serial_config: serial_connection.SerialConfig) -> Optional[int]:
    track_headers = arival_sq100.get_track_list(serial_config)
    if len(track_headers) == 0:
        print("no tracks found")
        return None
    latest = sorted(track_headers, key=lambda t: t.date)[-1]
    return latest.id
