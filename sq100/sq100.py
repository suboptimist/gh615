#! /usr/bin/env python

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


import argparse
import configparser
import logging
from sq100.serial_connection import SerialConfig
from typing import List
import tabulate

from sq100 import arival_sq100
from sq100.gpx import tracks_to_gpx
from sq100.utilities import parse_range

logging.basicConfig(filename="sq100.log", level=logging.DEBUG)


class SQ100:

    config: SerialConfig

    def __init__(self) -> None:
        config = configparser.ConfigParser()
        config.read('sq100.cfg')
        self.serial_comport = config['serial'].get("comport")
        self.serial_baudrate = config['serial'].getint('baudrate')
        self.serial_timeout = config['serial'].getfloat('timeout')

    def download_latest(self) -> None:
        track_headers = arival_sq100.get_track_list(self.config)
        if len(track_headers) == 0:
            print('no tracks found')
            return
        latest = sorted(track_headers, key=lambda t: t.date)[-1]
        print("latest track: %s, %s m, %s" %
              (latest.date, latest.distance, latest.duration))
        tracks = arival_sq100.get_tracks(self.config, [latest.id])
        tracks_to_gpx(
            tracks, "track-%s.gpx" % latest.date.strftime("%Y-%m-%d-%H-%M-%S"))

    def download_tracks(
        self, track_ids: List[int] = [], merge: bool = False
    ) -> None:
        if len(track_ids) == 0:
            return
        tracks = arival_sq100.get_tracks(
            config=self.config, track_ids=track_ids)
        if merge:
            tracks_to_gpx(tracks, "downloaded_tracks.gpx")
            return
        for track in tracks:
            tracks_to_gpx([track], "downloaded_tracks-%s.gpx" % track.info.id)

    def show_tracklist(self) -> None:
        tracks = arival_sq100.get_track_list(self.config)
        if tracks:
            table = [[track.id, track.date, track.distance, track.duration,
                      track.no_track_points, track.no_laps,
                      track.memory_block_index]
                     for track in tracks]
            headers = ["id", "date", "distance", "duration",
                       "trkpnts", "laps", "mem. index"]
            print(tabulate.tabulate(table, headers=headers))
        else:
            print('no tracks found')


gpl_disclaimer = """
SQ100 - Serial Communication with the a-rival SQ100 heart rate computer
Copyright (C) 2017  Timo Nachstedt

SQ100 is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

SQ100 is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

welcome_msg = """SQ100  Copyright (C) 2017  Timo Nachstedt
This program comes with ABSOLUTELY NO WARRANTY. SQ100 free software, and you
are welcome to redistribute it under certain conditions;
type `license' for details.

Welcome to SQ100. Type help or ? to list commands."""


def main() -> None:
    sq100 = SQ100()

    description = (
        'Serial Communication with the Arival SQ100 heart rate computer')
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-c", "--comport",
        help="comport for serial communication",
        default=sq100.serial_comport)
    parser.add_argument(
        "-b", "--baudrate",
        help="baudrate for serial communication",
        type=int,
        default=sq100.serial_baudrate)
    parser.add_argument(
        "-t", "--timeout",
        help="timeout for serial communication",
        type=int,
        default=sq100.serial_timeout)
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list")

    parser_download = subparsers.add_parser("download")
    parser_download.add_argument(
        "track_ids",
        help="list of track ids to download",
        type=parse_range,
        nargs='?', default=[])
    parser_download.add_argument(
        "-f", "--format",
        help="the format to export to",
        choices=['gpx'])
    parser_download.add_argument(
        "-m", "--merge",
        help="merge into single file?",
        action="store_true")
    parser_download.add_argument(
        "-l", "--latest",
        help="download latest track",
        action="store_true")

    args = parser.parse_args()
    sq100.config.port = args.comport
    sq100.config.baudrate = args.baudrate
    sq100.config.timeout = args.timeout

    if args.command == "list":
        sq100.show_tracklist()
    elif args.command == "download":
        if args.latest:
            sq100.download_latest()
        sq100.download_tracks(track_ids=args.track_ids, merge=args.merge)


if __name__ == "__main__":
    main()
