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
from dataclasses import dataclass
import functools
import datetime
import logging
import struct

from typing import List, NamedTuple, Tuple

from sq100.exceptions import SQ100MessageException
from sq100.data_types import Lap, Track, TrackPoint, TrackInfo
from sq100.serial_connection import SerialConnection, SerialConfig

logger = logging.getLogger(__name__)


class Message(NamedTuple):
    command: int
    payload_length: int
    parameter: bytes
    checksum: int


@dataclass
class TrackHead:
    date: datetime.datetime
    duration: datetime.timedelta
    no_laps: int
    distance: int
    no_track_points: int


@ dataclass
class TrackListEntry:
    date: datetime.datetime
    no_laps: int
    duration: datetime.timedelta
    distance: int
    no_track_points: int
    memory_block_index: int
    id: int


def head_is_compatible_to_track(
        head: TrackHead, track_info: TrackInfo) -> bool:
    return (
        head.date == track_info.date
        and head.duration == track_info.duration
        and head.no_laps == track_info.no_laps
        and head.distance == track_info.distance
        and head.no_track_points == track_info.no_track_points)


def calc_checksum(payload: bytes) -> int:
    payload_len = struct.pack("H", len(payload))
    checksum = functools.reduce(lambda x, y: x ^ y, payload_len + payload)
    return checksum


def create_message(command: int, parameter: bytes = b'') -> bytes:
    start_sequence = 0x02
    payload = bytes([command]) + parameter
    payload_length = len(payload)
    checksum = calc_checksum(payload)
    return struct.pack(
        ">BH%dsB" % len(payload),
        start_sequence, payload_length, payload, checksum)


def is_get_tracks_finish_message(msg: Message) -> bool:
    return msg.command == 0x8a


def pack_get_tracks_parameter(memory_indices: List[int]) -> bytes:
    no_tracks = len(memory_indices)
    return struct.pack(">H%dH" % no_tracks, no_tracks, *memory_indices)


def process_get_tracks_lap_info_msg(
        expected_track_info: TrackInfo, msg: Message) -> List[Lap]:
    logger.debug("processing get_tracks lap info msg")
    logger.debug("track: %s", expected_track_info)
    trackhead, laps = unpack_lap_info_parameter(msg.parameter)
    logger.debug("trackhead: %s", trackhead)
    logger.debug("laps: %s", laps)
    if not head_is_compatible_to_track(
            head=trackhead, track_info=expected_track_info):
        raise SQ100MessageException("unexpected track header")
    return laps


def process_get_tracks_track_info_msg(msg: Message) -> TrackInfo:
    logger.debug("processing get_tracks track info msg")
    track_info = unpack_track_info_parameter(msg.parameter)
    logger.debug("new track: %s", track_info)
    return track_info


def process_get_tracks_track_points_msg(
        expected_track_info: TrackInfo,
        expected_session_start: int,
        msg: Message) -> List[TrackPoint]:
    logger.debug("processing get_track track points msg")
    logger.debug("track = %s", expected_track_info)
    trackhead, session_indices, track_points = unpack_track_point_parameter(
        msg.parameter)
    logger.debug("trackhead = %s", trackhead)
    logger.debug("session_indices = %s", session_indices)
    logger.debug("no_track_points = %s", len(track_points))
    if not head_is_compatible_to_track(head=trackhead,
                                       track_info=expected_track_info):
        raise SQ100MessageException('unexpected track header')
    if session_indices[0] != expected_session_start:
        raise SQ100MessageException(
            "unexpectes session start ("
            + ("session_indices : %d,%d, " % session_indices)
            + ("expected session start: %d)" % expected_session_start))
    if session_indices[1] - session_indices[0] + 1 != len(track_points):
        raise SQ100MessageException(
            'session indices incompatible to number of received track '
            'points')
    logger.debug('adding trackpoints %i-%i', *session_indices)
    return track_points


def unpack_lap_info_parameter(
        parameter: bytes) -> Tuple[TrackHead, List[Lap]]:
    TrackHeader = collections.namedtuple('TrackHeader', [
        'year', 'month', 'day', 'hour', 'minute', 'second',
        'no_points', 'duration', 'distance',
        'no_laps', 'NA_1', 'msg_type'])
    t = TrackHeader._make(
        struct.unpack(">6B3IH8sB", parameter[:29]))
    if t.msg_type != 0xAA:
        raise SQ100MessageException("wrong get_tracks message type")
    track = TrackHead(
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


def unpack_track_info_parameter(parameter: bytes) -> TrackInfo:
    TrackHeader = collections.namedtuple('TrackHeader', [
        'year', 'month', 'day', 'hour', 'minute', 'second',
        'no_points', 'duration', 'distance',
        'no_laps', 'NA_1', 'memory_block_index', 'NA_2', 'id',
        'msg_type'])
    header = TrackHeader._make(
        struct.unpack(">6B3I5HB", parameter[:29]))
    if header.msg_type != 0x00:
        raise SQ100MessageException("wrong get_tracks message type")
    TrackData = collections.namedtuple('TrackInfo', [
        'calories', 'NA_1', 'max_speed', 'max_heart_rate',
        'avg_heart_rate', 'asc_height', 'des_height', 'min_height',
        'max_height', 'NA_2'])
    info = TrackData._make(
        struct.unpack(">3H2B4H13s", parameter[29:]))
    track = TrackInfo(
        date=datetime.datetime(
            2000 + header.year, header.month, header.day,
            header.hour, header.minute, header.second),
        no_track_points=header.no_points,
        duration=datetime.timedelta(
            seconds=round(header.duration / 10, 1)),
        distance=header.distance,
        no_laps=header.no_laps,
        memory_block_index=header.memory_block_index,
        id=header.id,
        calories=info.calories,
        max_speed=info.max_speed,
        max_heart_rate=info.max_heart_rate,
        avg_heart_rate=info.avg_heart_rate,
        ascending_height=info.asc_height,
        descending_height=info.des_height,
        min_height=info.min_height,
        max_height=info.max_height)
    return track


def unpack_track_point_parameter(
        parameter: bytes
) -> Tuple[TrackHead, Tuple[int, int], List[TrackPoint]]:
    TrackHeader = collections.namedtuple('TrackHeader', [
        'year', 'month', 'day', 'hour', 'minute', 'second',
        'no_points', 'duration', 'distance',
        'no_laps', 'first_session_index', 'last_session_index',
        'msg_type'])
    t = TrackHeader._make(
        struct.unpack(">6B3IH2IB", parameter[:29]))
    if t.msg_type != 0x55:
        raise SQ100MessageException("wrong get_tracks message type")
    track = TrackHead(
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


def unpack_track_list_parameter(parameter: bytes) -> List[TrackListEntry]:
    TrackHeader = collections.namedtuple('TrackHeader', [
        'year', 'month', 'day', 'hour', 'minute', 'second',
        'no_points', 'duration', 'distance',
        'lap_count', 'unused_1', 'memory_block_index', 'unused_2', 'id',
        'unused_3'])
    track_headers = map(
        TrackHeader._make,
        struct.iter_unpack(">6B3I5HB", parameter))
    tracks = [
        TrackListEntry(
            date=datetime.datetime(
                2000 + t.year, t.month, t.day, t.hour, t.minute, t.second),
            no_laps=t.lap_count,
            duration=datetime.timedelta(seconds=round(t.duration / 10, 1)),
            distance=t.distance,
            no_track_points=t.no_points,
            memory_block_index=t.memory_block_index,
            id=t.id)
        for t in track_headers]
    return tracks


def unpack_message(message: bytes) -> Message:
    msg = Message._make(
        struct.unpack(">BH%dsB" % (len(message) - 4), message))
    if msg.payload_length != len(msg.parameter):
        raise SQ100MessageException(
            "paylod has wrong length!\n"
            + ("Message says %d\n" % msg.payload_length)
            + ("Parameter length is %d" % len(msg.parameter)))
    if msg.checksum != calc_checksum(msg.parameter):
        raise SQ100MessageException("checksum wrong")
    return msg


def get_tracks(config: SerialConfig, track_ids: List[int]) -> List[Track]:
    with SerialConnection(config) as connection:
        return query_tracks(connection, track_ids)


def query_tracks(
        connection: SerialConnection, track_ids: List[int]) -> List[Track]:
    track_list = query_track_list(connection)
    memory_indices = track_ids_to_memory_indices(
        tracks=track_list, track_ids=track_ids)
    params = pack_get_tracks_parameter(memory_indices)
    msg = query(connection, command=0x80, parameter=params)
    tracks = []
    for _ in range(len(track_ids)):
        track_info = process_get_tracks_track_info_msg(msg)
        laps = process_get_tracks_lap_info_msg(
            expected_track_info=track_info,
            msg=query(connection, command=0x81))
        track_points: List[TrackPoint] = []
        while len(track_points) < track_info.no_track_points:
            track_points += process_get_tracks_track_points_msg(
                expected_track_info=track_info,
                expected_session_start=len(track_points),
                msg=query(connection, 0x81))
        tracks.append(Track(
            info=track_info, laps=laps, track_points=track_points))
        msg = query(connection, 0x81)
    if not is_get_tracks_finish_message(msg):
        raise SQ100MessageException('expected end of transmission message')
    logger.info("number of downloaded tracks: %d", len(tracks))
    return tracks


def track_ids_to_memory_indices(
        tracks: List[TrackListEntry], track_ids: List[int]) -> List[int]:
    index = {t.id: t.memory_block_index for t in tracks}
    memory_indices = [index[track_id] for track_id in track_ids]
    return memory_indices


def get_track_list(config: SerialConfig) -> List[TrackListEntry]:
    with SerialConnection(config) as connection:
        return query_track_list(connection)


def query_track_list(connection: SerialConnection) -> List[TrackListEntry]:
    msg = query(connection=connection, command=0x78)
    tracks = unpack_track_list_parameter(msg.parameter)
    logger.info('received list of %i tracks' % len(tracks))
    return tracks


def query(
        connection: SerialConnection,
        command: int,
        parameter: bytes = b'') -> Message:
    connection.write(create_message(command, parameter))
    # first, read three bytes to determine payload
    begin = connection.read(3)
    _, payload = struct.unpack(">BH", begin)
    rest = connection.read(payload + 1)  # +1 for checksum
    return unpack_message(begin + rest)
