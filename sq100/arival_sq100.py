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

import collections
import functools
import datetime
import logging
import struct

from sq100.exceptions import SQ100MessageException
from sq100.serial_connection import SerialConnection
from sq100.data_types import Lap, Track, TrackPoint


logger = logging.getLogger(__name__)

Message = collections.namedtuple("Message", [
    'command', 'payload_length', 'parameter', 'checksum'])


class ArivalSQ100(object):

    def __init__(self, port, baudrate, timeout):
        self.serial = SerialConnection(
            port=port, baudrate=baudrate, timeout=timeout)

    @staticmethod
    def _calc_checksum(payload):
        payload_len = struct.pack("H", len(payload))
        checksum = functools.reduce(lambda x, y: x ^ y, payload_len + payload)
        return checksum

    @staticmethod
    def _create_message(command, parameter=b''):
        start_sequence = 0x02
        payload = bytes([command]) + parameter
        payload_length = len(payload)
        checksum = ArivalSQ100._calc_checksum(payload)
        return struct.pack(">BH%dsB" % len(payload),
                           start_sequence, payload_length, payload, checksum)

    @staticmethod
    def _is_get_tracks_finish_message(msg):
        return msg.command == 0x8a

    @staticmethod
    def _pack_get_tracks_parameter(memory_indices):
        no_tracks = len(memory_indices)
        return struct.pack(">H%dH" % no_tracks, no_tracks, *memory_indices)

    @staticmethod
    def _process_get_tracks_lap_info_msg(track, msg):
        logger.debug("processing get_tracks lap info msg")
        logger.debug("track: %s", track)
        trackhead, laps = ArivalSQ100._unpack_lap_info_parameter(msg.parameter)
        logger.debug("trackhead: %s", trackhead)
        logger.debug("laps: %s", laps)
        if not track.compatible_to(trackhead):
            raise SQ100MessageException("unexpected track header")
        track.laps = laps
        return track

    @staticmethod
    def _process_get_tracks_track_info_msg(msg):
        logger.debug("processing get_tracks track info msg")
        track = ArivalSQ100._unpack_track_info_parameter(msg.parameter)
        logger.debug("new track: %s", track)
        return track

    @staticmethod
    def _process_get_tracks_track_points_msg(track, msg):
        logger.debug("processing get_track track points msg")
        logger.debug("track = %s", track)
        trackhead, session_indices, track_points = (
            ArivalSQ100._unpack_track_point_parameter(msg.parameter))
        logger.debug("trackhead = %s", trackhead)
        logger.debug("session_indices = %s", session_indices)
        logger.debug("no_track_points = %s", len(track_points))
        if not track.compatible_to(trackhead):
            raise SQ100MessageException('unexpected track header')
        if session_indices[0] != len(track.track_points):
            raise SQ100MessageException(
                "unexpectes session start ("
                + ("session_indicces : %d,%d, " % session_indices)
                + ("number of track points in track: %d)" %
                   len(track.track_points)))
        if session_indices[1] - session_indices[0] + 1 != len(track_points):
            raise SQ100MessageException(
                'session indices incompatible to number of received track '
                'points')
        logger.debug('adding trackpoints %i-%i', *session_indices)
        track.track_points.extend(track_points)
        return track

    def _query(self, command, parameter=b''):
        self.serial.write(self._create_message(command, parameter))
        "first, read three bytes to determine payload"
        begin = self.serial.read(3)
        _, payload = struct.unpack(">BH", begin)
        rest = self.serial.read(payload + 1)  # +1 for checksum
        return self._unpack_message(begin + rest)

    def _track_ids_to_memory_indices(self, track_ids):
        tracks = self.get_track_list()
        index = {t.id: t.memory_block_index for t in tracks}
        memory_indices = [index[track_id] for track_id in track_ids]
        return memory_indices

    @staticmethod
    def _unpack_lap_info_parameter(parameter):
        TrackHeader = collections.namedtuple('TrackHeader', [
            'year', 'month', 'day', 'hour', 'minute', 'second',
            'no_points', 'duration', 'distance',
            'no_laps', 'NA_1', 'msg_type'])
        t = TrackHeader._make(
            struct.unpack(">6B3IH8sB", parameter[:29]))
        if t.msg_type != 0xAA:
            raise SQ100MessageException("wrong get_tracks message type")
        track = Track(
            date=datetime.datetime(
                2000 + t.year, t.month, t.day, t.hour, t.minute, t.second),
            no_track_points=t.no_points,
            duration=datetime.timedelta(seconds=round(t.duration / 10, 1)),
            distance=t.distance,
            no_laps=t.no_laps)
        LapInfo = collections.namedtuple('LapInfo', [
            'duration', 'total_time', 'distance', 'calories',
            'NA_1', 'max_speed', 'max_heart_rate', 'avg_heart_rate',
            'min_height', 'max_height', 'NA_2', 'first_index', 'last_index'])
        lap_infos = map(
            LapInfo._make,
            struct.iter_unpack(">3I3H2B2H13s2H", parameter[29:]))
        laps = [
            Lap(duration=datetime.timedelta(
                seconds=round(lap.duration / 10, 1)),
                total_time=datetime.timedelta(
                    seconds=round(lap.total_time / 10, 1)),
                distance=lap.distance,
                calories=lap.calories,
                max_speed=lap.max_speed,
                max_heart_rate=lap.max_heart_rate,
                avg_heart_rate=lap.avg_heart_rate,
                min_height=lap.min_height,
                max_height=lap.max_height,
                first_index=lap.first_index,
                last_index=lap.last_index)
            for lap in lap_infos]
        return track, laps

    @staticmethod
    def _unpack_message(message):
        msg = Message._make(
            struct.unpack(">BH%dsB" % (len(message) - 4), message))
        if msg.payload_length != len(msg.parameter):
            raise SQ100MessageException(
                "paylod has wrong length!\n"
                + ("Message says %d\n" % msg.payload_length)
                + ("Parameter length is %d" % len(msg.parameter)))
        if msg.checksum != ArivalSQ100._calc_checksum(msg.parameter):
            raise SQ100MessageException("checksum wrong")
        return msg

    @staticmethod
    def _unpack_track_info_parameter(parameter):
        TrackHeader = collections.namedtuple('TrackHeader', [
            'year', 'month', 'day', 'hour', 'minute', 'second',
            'no_points', 'duration', 'distance',
            'no_laps', 'NA_1', 'memory_block_index', 'NA_2', 'id',
            'msg_type'])
        header = TrackHeader._make(
            struct.unpack(">6B3I5HB", parameter[:29]))
        if header.msg_type != 0x00:
            raise SQ100MessageException("wrong get_tracks message type")
        TrackInfo = collections.namedtuple('TrackInfo', [
            'calories', 'NA_1', 'max_speed', 'max_heart_rate',
            'avg_heart_rate', 'asc_height', 'des_height', 'min_height',
            'max_height', 'NA_2'])
        info = TrackInfo._make(
            struct.unpack(">3H2B4H13s", parameter[29:]))
        track = Track(
            date=datetime.datetime(
                2000 + header.year, header.month, header.day,
                header.hour, header.minute, header.second),
            no_track_points=header.no_points,
            duration=datetime.timedelta(
                seconds=round(header.duration / 10, 1)),
            distance=header.distance,
            no_laps=header.no_laps,
            memory_block_index=header.memory_block_index,
            track_id=header.id,
            calories=info.calories,
            max_speed=info.max_speed,
            max_heart_rate=info.max_heart_rate,
            avg_heart_rate=info.avg_heart_rate,
            ascending_height=info.asc_height,
            descending_height=info.des_height,
            min_height=info.min_height,
            max_height=info.max_height)
        return track

    @staticmethod
    def _unpack_track_list_parameter(parameter):
        TrackHeader = collections.namedtuple('TrackHeader', [
            'year', 'month', 'day', 'hour', 'minute', 'second',
            'no_points', 'duration', 'distance',
            'lap_count', 'unused_1', 'memory_block_index', 'unused_2', 'id',
            'unused_3'])
        track_headers = map(
            TrackHeader._make,
            struct.iter_unpack(">6B3I5HB", parameter))
        tracks = [
            Track(
                date=datetime.datetime(
                    2000 + t.year, t.month, t.day, t.hour, t.minute, t.second),
                no_laps=t.lap_count,
                duration=datetime.timedelta(seconds=round(t.duration / 10, 1)),
                distance=t.distance,
                no_track_points=t.no_points,
                memory_block_index=t.memory_block_index,
                track_id=t.id)
            for t in track_headers]
        return tracks

    @staticmethod
    def _unpack_track_point_parameter(parameter):
        TrackHeader = collections.namedtuple('TrackHeader', [
            'year', 'month', 'day', 'hour', 'minute', 'second',
            'no_points', 'duration', 'distance',
            'no_laps', 'first_session_index', 'last_session_index',
            'msg_type'])
        t = TrackHeader._make(
            struct.unpack(">6B3IH2IB", parameter[:29]))
        if t.msg_type != 0x55:
            raise SQ100MessageException("wrong get_tracks message type")
        track = Track(
            date=datetime.datetime(
                2000 + t.year, t.month, t.day, t.hour, t.minute, t.second),
            no_track_points=t.no_points,
            duration=datetime.timedelta(seconds=round(t.duration / 10, 1)),
            distance=t.distance,
            no_laps=t.no_laps)
        session_indices = (t.first_session_index, t.last_session_index)
        TrackPointData = collections.namedtuple('TrackPointData', [
            'latitude', 'longitude', 'altitude', 'NA_1', 'speed',
            'heart_rate', 'NA_2', 'interval_time', 'NA_3'])
        trackpoint_data = map(
            TrackPointData._make,
            struct.iter_unpack('>2i3HBHH6s', parameter[29:]))
        trackpoints = [
            TrackPoint(
                latitude=round(t.latitude * 1e-6, 6),
                longitude=round(t.longitude * 1e-6, 6),
                altitude=t.altitude,
                speed=round(t.speed * 1e-2, 2),
                heart_rate=t.heart_rate,
                interval=datetime.timedelta(
                    seconds=round(t.interval_time * 1e-1, 1)))
            for t in trackpoint_data]
        return track, session_indices, trackpoints

    def connect(self):
        self.serial.connect()

    def disconnect(self):
        self.serial.disconnect()

    def get_track_list(self):
        msg = self._query(0x78)
        tracks = self._unpack_track_list_parameter(msg.parameter)
        logger.info('received list of %i tracks' % len(tracks))
        return tracks

    def get_tracks(self, track_ids):
        memory_indices = self._track_ids_to_memory_indices(track_ids)
        params = self._pack_get_tracks_parameter(memory_indices)
        msg = self._query(0x80, params)
        tracks = []
        for _ in range(len(track_ids)):
            track = self._process_get_tracks_track_info_msg(msg)
            msg = self._query(0x81)
            self._process_get_tracks_lap_info_msg(track, msg)
            while not track.complete():
                msg = self._query(0x81)
                self._process_get_tracks_track_points_msg(track, msg)
            track.update_track_point_times()
            tracks.append(track)
            msg = self._query(0x81)
        if not self._is_get_tracks_finish_message(msg):
            raise SQ100MessageException('expected end of transmission message')
        logger.info("number of downloaded tracks: %d", len(tracks))
        return tracks
