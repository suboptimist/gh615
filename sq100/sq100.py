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
import cmd
import configparser
import logging
import tabulate

from sq100.arival_sq100 import ArivalSQ100
from sq100.exceptions import SQ100SerialException
from sq100.gpx import tracks_to_gpx
from sq100.utilities import parse_range

logging.basicConfig(filename="sq100.log", level=logging.DEBUG)


class SQ100(object):

    def __init__(self):
        config = configparser.SafeConfigParser()
        config.read('sq100.cfg')
        self.serial_comport = config['serial'].get("comport")
        self.serial_baudrate = config['serial'].get('baudrate')
        self.serial_timeout = config['serial'].get('timeout')
        self.computer = None

    def connect(self):
        self.computer = ArivalSQ100(port=self.serial_comport,
                                    baudrate=self.serial_baudrate,
                                    timeout=self.serial_timeout)
        try:
            self.computer.connect()
            return True
        except SQ100SerialException:
            print("Connection to device failed! Check serial settings.")
            return False

    def delete_all_tracks(self):
        print("Sorry! Deleting all tracks is not yet implemented")
        return
        print("Delete all Tracks")
        input("warning, DELETING ALL TRACKS").strip()
        results = self.computer.delete_all_tracks()
        print('Deleted all Tracks:', results)

    def delete_all_waypoints(self):
        print("Sorry! Deleting all waypoints is not yet implemented")
        return
        print("Delete all Waypoints")
        input("WARNING DELETING ALL WAYPOINTS").strip()
        results = self.computer.delete_all_waypoints()
        print('Formatted all Waypoints:', results)

    def device_info(self):
        print('Sorry! Showing Device Info is not yet implemented.')
        return
        unit = self.computer.getUnitInformation()
        print("* %s waypoints on watch" % unit['waypoint_count'])
        print("* %s trackpoints on watch" % unit['trackpoint_count'])

    def download_latest(self):
        track_headers = self.computer.get_track_list()
        if len(track_headers) == 0:
            print('no tracks found')
            return
        latest = sorted(track_headers, key=lambda t: t.date)[-1]
        print("latest track: %s, %s m, %s" %
              (latest.date, latest.distance, latest.duration))
        tracks = self.computer.get_tracks([latest.id])
        tracks_to_gpx(
            tracks, "track-%s.gpx" % latest.date.strftime("%Y-%m-%d-%H-%M-%S"))

    def download_tracks(self, track_ids=[], merge=False):
        if len(track_ids) == 0:
            return
        tracks = self.computer.get_tracks(track_ids)
        if merge:
            tracks_to_gpx(tracks, "downloaded_tracks.gpx")
            return
        for track in tracks:
            tracks_to_gpx([track], "downloaded_tracks-%s.gpx" % track.id)

    def download_waypoints(self):
        print("Sorry! Downloading way points is not yet implemented.")
        return
        print("Download Waypoints")
        waypoints = self.computer.get_waypoints()
        results = self.computer.exportWaypoints(waypoints)
        print('exported Waypoints to', results)

    def export_all_tracks(self):
        print("Sorry! Exporting all tracks is not yet implemented.")
        return

    def show_tracklist(self):
        tracks = self.computer.get_track_list()
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

    def upload_tracks(self):
        print("Sorry! Uploading tracks is not yet implemented.")
        return
        # print("Upload Tracks")
        # files = glob.glob(
        #     os.path.join(Utilities.getAppPrefix(), "import", "*.gpx"))
        # for i, format in enumerate(files):
        #     (filepath, filename) = os.path.split(format)
        #     # (shortname, extension) = os.path.splitext(filename)
        #     print('[%i] = %s' % (i, filename))

        # fileId = input("enter number(s) [space delimited] ").strip()
        # fileIds = fileId.split(' ')

        # filesToBeImported = []
        # for fileId in fileIds:
        #     filesToBeImported.append(files[int(fileId)])

        # tracks = self.computer.import_tracks(filesToBeImported)
        # results = self.computer.set_tracks(tracks)
        # print('successfully uploaded tracks ', str(results))

    def upload_waypoints(self):
        print("Sorry! Uploading way points is not yet implemented.")
        return
        print("Upload Waypoints")
        waypoints = self.computer.import_waypoints()
        results = self.computer.set_waypoints(waypoints)
        print('Imported %i Waypoints' % results)


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


class SQ100Shell(cmd.Cmd):
    intro = welcome_msg
    prompt = '(sq100)'

    def __init__(self, sq100):
        super().__init__()
        self.sq100 = sq100

#     def do_delete_all_tracks(self, arg):
#         "delete all tracks on device"
#         self.sq100.delete_all_tracks()
#
#     def do_delete_all_waypoints(self, arg):
#         "delete all waypoints on device"
#         self.sq100.delete_all_waypoints()

    def do_download(self, arg):
        "export selected tracks into file: export 2,5"
        if arg == "latest":
            self.sq100.download_latest()
        else:
            track_ids = parse_range(arg)
            self.sq100.download_tracks(track_ids=track_ids)

#     def do_export_all(self, arg):
#         "export all tracks"
#         self.sq100.export_all_tracks()

    def do_license(self, arg):
        print(gpl_disclaimer)

    def do_list(self, arg):
        "show list of all tracks on the device: list"
        self.sq100.show_tracklist()

    def do_quit(self, arg):
        "Exit the application"
        return True

#     def do_upload(self, arg):
#         "upload tracks"
#         self.sq100.upload_tracks()
#         pass
#
#     def do_wpt_download(self, arg):
#         "download waypoints"
#         self.sq100.download_waypoints()
#
#     def do_wpt_upload(self, arg):
#         "upload waypoints"
#         self.sq100.upload_waypoints()


def main():
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

#     parser.add_argument(
#         "-i", "--input",
#         help="input file(s)",
#         action="append")
#     parser.add_argument(
#         "-o", "--output",
#         help="the path to output to")

    args = parser.parse_args()
    sq100.serial_comport = args.comport
    sq100.serial_baudrate = args.baudrate
    sq100.serial_timeout = args.timeout

    if sq100.connect() is False:
        return

    if args.command is None:
        SQ100Shell(sq100).cmdloop()
    elif args.command == "list":
        sq100.show_tracklist()
    elif args.command == "download":
        if args.latest:
            sq100.download_latest()
        sq100.download_tracks(track_ids=args.track_ids, merge=args.merge)


if __name__ == "__main__":
    main()
