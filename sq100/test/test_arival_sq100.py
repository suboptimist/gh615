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

import datetime
import pytest
import struct
from pytest_mock import MockerFixture

from sq100.test.dummies import make_track_info, make_track_points
from sq100 import arival_sq100
from sq100 import serial_connection
from sq100.exceptions import SQ100MessageException
from sq100.data_types import Lap, TrackInfo, TrackPoint


def make_track_head(
        date: datetime.datetime = datetime.datetime(1987, 12, 19),
        duration: datetime.timedelta = datetime.timedelta(seconds=0),
        no_laps: int = 0,
        distance: int = 0,
        no_track_points: int = 0,
) -> arival_sq100.TrackHead:
    return arival_sq100.TrackHead(
        date=date, duration=duration, no_laps=no_laps,
        distance=distance, no_track_points=no_track_points)


def test_calc_checksum__returns_corect_value_for_simple_payload() -> None:
    payload = b"\x45\x73\xAF\x20"
    checksum = 4 ^ 0x45 ^ 0x73 ^ 0xAF ^ 0x20
    assert(checksum == arival_sq100.calc_checksum(payload))


def test_create_message__return_correct_bytest_for_empty_parameter() -> None:
    message = arival_sq100.create_message(command=0x78)
    assert(message == b'\x02\x00\x01\x78\x79')


def test_create_message__return_correct_bytest_with_parameter() -> None:
    message = arival_sq100.create_message(command=0x78, parameter=b'\x42')
    assert(message == b'\x02\x00\x02\x78\x42\x38')


def make_message(
        command: int = 0x00,
        parameter: bytes = b''
) -> arival_sq100.Message:
    return arival_sq100.Message(
        command=command,
        payload_length=0,
        parameter=parameter,
        checksum=0)


def make_lap(first_index: int = 0) -> Lap:
    return Lap(
        duration=datetime.timedelta(seconds=0),
        total_time=datetime.timedelta(seconds=0),
        distance=0.,
        calories=0.,
        max_speed=0.,
        max_heart_rate=0.,
        avg_heart_rate=0.,
        min_height=0.,
        max_height=0.,
        first_index=first_index,
        last_index=0,
    )


def test_is_get_tracks_finish_message__returns_true_for_0x8a_command() -> None:
    msg = make_message(command=0x8a)
    assert arival_sq100.is_get_tracks_finish_message(msg) is True


def test_is_get_tracks_finish_message__returns_false_for_other_command(
) -> None:
    msg = make_message(command=0x80)
    assert arival_sq100.is_get_tracks_finish_message(msg) is False


def test_pack_get_tracks_parameter__returns_correct_pack() -> None:
    memory_indices = [10, 22, 50]
    parameter = arival_sq100.pack_get_tracks_parameter(memory_indices)
    assert parameter == bytes([0, 3, 0, 10, 0, 22, 0, 50])


def test_process_get_tracks_lap_info_msg__returns_correct_laps(
        mocker: MockerFixture) -> None:
    msg = make_message(parameter=b'parameter')
    unpack_lap_info_mock = mocker.patch(
        'sq100.arival_sq100.unpack_lap_info_parameter')
    unpack_lap_info_mock.return_value = (
        make_track_head(
            date=datetime.datetime(1987, 12, 19),
            duration=datetime.timedelta(seconds=4),
            no_laps=1, distance=2, no_track_points=3),
        [make_lap(first_index=42)])

    laps = arival_sq100.process_get_tracks_lap_info_msg(
        expected_track_info=make_track_info(
            date=datetime.datetime(1987, 12, 19),
            duration=datetime.timedelta(seconds=4),
            no_laps=1, distance=2, no_track_points=3),
        msg=msg)

    assert len(laps) == 1
    assert laps[0].first_index == 42
    unpack_lap_info_mock.assert_called_once_with(b'parameter')


def test_process_get_tracks_lap_info_msg__raises_if_tracks_are_incompatible(
        mocker: MockerFixture) -> None:
    msg = make_message(parameter=b'parameter')
    unpack_lap_info_mock = mocker.patch(
        'sq100.arival_sq100.unpack_lap_info_parameter')
    unpack_lap_info_mock.return_value = (
        make_track_head(no_laps=2), [make_lap(first_index=42)])

    with pytest.raises(SQ100MessageException):
        arival_sq100.process_get_tracks_lap_info_msg(
            expected_track_info=make_track_info(no_laps=3),
            msg=msg)


def test_process_get_tracks_track_info_msg(mocker: MockerFixture) -> None:
    msg = make_message(parameter=b'parameter')
    unpack_track_info_mock = mocker.patch(
        'sq100.arival_sq100.unpack_track_info_parameter')
    mock_return_track = make_track_info(id=20)
    unpack_track_info_mock.return_value = mock_return_track

    track = arival_sq100.process_get_tracks_track_info_msg(msg)

    unpack_track_info_mock.assert_called_once_with(msg.parameter)
    assert track == mock_return_track


def test_process_get_tracks_track_points_msg__returns_points(
        mocker: MockerFixture) -> None:
    msg = make_message(parameter=b"paramster")
    track_info = make_track_info()
    unpack_mock = mocker.patch(
        'sq100.arival_sq100.unpack_track_point_parameter')
    returned_track = make_track_info()
    returned_track_points = make_track_points(
        [{'latitude': 3.}, {'latitude': 4.}, {'latitude': 5.}])
    unpack_mock.return_value = returned_track, (2, 4), returned_track_points

    track_points = arival_sq100.process_get_tracks_track_points_msg(
        expected_track_info=track_info, expected_session_start=2, msg=msg)

    assert len(track_points) == 3
    assert track_points[0].latitude == 3.
    assert track_points[1].latitude == 4.
    assert track_points[2].latitude == 5.


def test_process_get_tracks_track_points_msg__raises_if_track_is_incompatible(
        mocker: MockerFixture) -> None:
    msg = make_message(parameter=b"paramster")
    unpack_mock = mocker.patch(
        'sq100.arival_sq100.unpack_track_point_parameter')
    unpack_mock.return_value = (
        make_track_head(no_laps=2),
        (0, 2),
        make_track_points([{}, {}, {}]))

    with pytest.raises(SQ100MessageException):
        arival_sq100.process_get_tracks_track_points_msg(
            expected_track_info=make_track_info(no_laps=3),
            expected_session_start=0, msg=msg)


def test_process_get_tracks_track_points_msg__raises_if_session_start_is_wrong(
        mocker: MockerFixture) -> None:
    msg = make_message(parameter=b"paramster")
    track_info = make_track_info()
    unpack_mock = mocker.patch(
        'sq100.arival_sq100.unpack_track_point_parameter')
    returned_track = make_track_info()
    unpack_mock.return_value = returned_track, (1, 2), make_track_points([
        {}, {}])

    with pytest.raises(SQ100MessageException):
        arival_sq100.process_get_tracks_track_points_msg(
            expected_track_info=track_info, expected_session_start=0, msg=msg)


def test_process_get_tracks_track_points_msg__raises_if_session_len_is_wrong(
        mocker: MockerFixture) -> None:
    msg = make_message(parameter=b"paramster")
    track = make_track_info()
    unpack_mock = mocker.patch(
        'sq100.arival_sq100.unpack_track_point_parameter')
    returned_track = make_track_info()
    unpack_mock.return_value = returned_track, (0, 10), make_track_points([
        {}, {}])

    with pytest.raises(SQ100MessageException):
        arival_sq100.process_get_tracks_track_points_msg(
            expected_track_info=track,
            expected_session_start=0,
            msg=msg)


def make_lap_info_trackhead_pack(
        date: datetime.datetime,
        no_track_points: int,
        duration: datetime.timedelta,
        no_laps: int,
        distance: float,
        msg_type: int
) -> bytes:
    return struct.pack(
        ">6B3IH8sB",
        date.year - 2000, date.month, date.day,
        date.hour, date.minute, date.second,
        no_track_points,
        round(duration.total_seconds() * 10),
        distance,
        no_laps,
        b'',
        msg_type)


def make_lap_info_lap_pack(
        duration: datetime.timedelta,
        total_time: datetime.timedelta,
        distance: int,
        calories: int,
        max_speed: int,
        max_heart_rate: int,
        avg_heart_rate: int,
        min_height: int,
        max_height: int,
        first_index: int,
        last_index: int
) -> bytes:
    return struct.pack(
        ">3I3H2B2H13s2H",
        round(duration.total_seconds() * 10),
        round(total_time.total_seconds() * 10),
        distance, calories,
        0, max_speed, max_heart_rate, avg_heart_rate,
        min_height, max_height, b'',
        first_index, last_index)


def test_unpack_lap_info_parameter__unpacks_data_correctly() -> None:
    parameter = (
        make_lap_info_trackhead_pack(
            date=datetime.datetime(2010, 1, 2, 3, 4, 5), no_track_points=10,
            duration=datetime.timedelta(seconds=2345.6), distance=11,
            no_laps=2, msg_type=0xAA)
        + make_lap_info_lap_pack(
            duration=datetime.timedelta(seconds=22.2),
            total_time=datetime.timedelta(seconds=222.2),
            distance=20, calories=21, max_speed=22, max_heart_rate=23,
            avg_heart_rate=24, min_height=25, max_height=26,
            first_index=27, last_index=28)
        + make_lap_info_lap_pack(
            duration=datetime.timedelta(seconds=33.3),
            total_time=datetime.timedelta(seconds=333.3),
            distance=30, calories=31, max_speed=32, max_heart_rate=33,
            avg_heart_rate=34, min_height=35, max_height=36,
            first_index=37, last_index=38))

    track, laps = arival_sq100.unpack_lap_info_parameter(parameter)

    assert track == arival_sq100.TrackHead(
        date=datetime.datetime(2010, 1, 2, 3, 4, 5),
        duration=datetime.timedelta(seconds=2345.6),
        no_track_points=10, distance=11, no_laps=2)
    assert laps == [
        Lap(duration=datetime.timedelta(seconds=22.2),
            total_time=datetime.timedelta(seconds=222.2),
            distance=20, calories=21, max_speed=22, max_heart_rate=23,
            avg_heart_rate=24, min_height=25, max_height=26,
            first_index=27, last_index=28),
        Lap(duration=datetime.timedelta(seconds=33.3),
            total_time=datetime.timedelta(seconds=333.3),
            distance=30, calories=31, max_speed=32, max_heart_rate=33,
            avg_heart_rate=34, min_height=35, max_height=36,
            first_index=37, last_index=38)]


def test_unpack_lap_info_parameter__raises_if_message_type_is_wrong() -> None:
    parameter = make_lap_info_trackhead_pack(
        date=datetime.datetime(2010, 1, 2, 3, 4, 5), no_track_points=10,
        duration=datetime.timedelta(seconds=2345.6), distance=11,
        no_laps=0, msg_type=0xAB)

    with pytest.raises(SQ100MessageException):
        arival_sq100.unpack_lap_info_parameter(parameter)


def make_track_info_pack(
        msg_type: int,
        date: datetime.datetime,
        no_track_points: int,
        duration: datetime.timedelta,
        distance: int,
        no_laps: int,
        memory_block_index: int,
        track_id: int,
        calories: int,
        max_speed: int,
        max_heart_rate: int,
        avg_heart_rate: int,
        asc_height: int,
        des_height: int,
        min_height: int,
        max_height: int,
) -> bytes:
    return struct.pack(
        ">6B3I5HB3H2B4H13s",
        date.year - 2000, date.month, date.day,
        date.hour, date.minute, date.second,
        no_track_points,
        round(duration.total_seconds() * 10),
        distance,
        no_laps, 0, memory_block_index, 0, track_id,
        msg_type,
        calories, 0, max_speed,
        max_heart_rate, avg_heart_rate,
        asc_height, des_height, min_height, max_height,
        b'')


def test_unpack_track_info_parameter__unpacks_correct_data() -> None:
    date = datetime.datetime(2016, 7, 23, 14, 30, 11)
    duration = datetime.timedelta(seconds=2345.9)
    parameter = make_track_info_pack(
        msg_type=0, date=date, no_track_points=1, duration=duration,
        distance=2, no_laps=3, memory_block_index=4, track_id=5, calories=6,
        max_speed=7, max_heart_rate=8, avg_heart_rate=9, asc_height=10,
        des_height=11, min_height=12, max_height=13,
    )

    track_info = arival_sq100.unpack_track_info_parameter(parameter)

    assert track_info == TrackInfo(
        date=date, no_track_points=1, duration=duration, distance=2, no_laps=3,
        memory_block_index=4, id=5, calories=6, max_speed=7, max_heart_rate=8,
        avg_heart_rate=9, ascending_height=10, descending_height=11,
        min_height=12, max_height=13)


def test_unpack_track_info_parameter__raises_if_msg_type_is_wrong() -> None:
    parameter = make_track_info_pack(
        msg_type=1, date=datetime.datetime(2016, 7, 23, 14, 30, 11),
        no_track_points=1, duration=datetime.timedelta(seconds=12),
        distance=2, no_laps=3, memory_block_index=4, track_id=5, calories=6,
        max_speed=7, max_heart_rate=8, avg_heart_rate=9, asc_height=10,
        des_height=11, min_height=12, max_height=13,
    )
    with pytest.raises(SQ100MessageException):
        arival_sq100.unpack_track_info_parameter(parameter)


def make_track_point_trackhead_pack(
        msg_type: int,
        date: datetime.datetime,
        no_track_points: int,
        duration: datetime.timedelta,
        distance: int,
        no_laps: int,
        session_start: int,
        session_last: int) -> bytes:
    return struct.pack(
        ">6B3IH2IB",
        date.year - 2000, date.month, date.day,
        date.hour, date.minute, date.second,
        no_track_points, round(duration.total_seconds() * 10),
        distance, no_laps, session_start, session_last, msg_type)


def make_track_point_pack(
        latitude: float, longitude: float, altitude: int, speed: float,
        heart_rate: int, interval: datetime.timedelta) -> bytes:
    return struct.pack(
        ">2i3HB2H6s",
        int(round(latitude * 1e6)), int(round(longitude * 1e6)),
        altitude, 0, int(round(speed * 100)), heart_rate, 0,
        int(round(interval.total_seconds() * 10)), b'')


def test_unpack_track_point_parameter__unpacks_correct_data() -> None:
    parameter = (
        make_track_point_trackhead_pack(
            date=datetime.datetime(2001, 2, 3, 4, 5, 6),
            no_track_points=1, duration=datetime.timedelta(seconds=100.0),
            distance=2, no_laps=3, session_start=4, session_last=5,
            msg_type=0x55)
        + make_track_point_pack(
            latitude=51.123456, longitude=9.234567, altitude=101, speed=11.11,
            heart_rate=102, interval=datetime.timedelta(seconds=10.1))
        + make_track_point_pack(
            latitude=-12.345678, longitude=-87.654321, altitude=201,
            speed=22.22, heart_rate=202,
            interval=datetime.timedelta(seconds=20.2)))

    track, session, track_points = arival_sq100.unpack_track_point_parameter(
        parameter)

    assert track == arival_sq100.TrackHead(
        date=datetime.datetime(2001, 2, 3, 4, 5, 6), no_track_points=1,
        duration=datetime.timedelta(seconds=100.0), distance=2,
        no_laps=3)
    assert session == (4, 5)
    assert track_points == [
        TrackPoint(
            latitude=51.123456, longitude=9.234567, altitude=101, speed=11.11,
            heart_rate=102, interval=datetime.timedelta(seconds=10.1)),
        TrackPoint(
            latitude=-12.345678, longitude=-87.654321, altitude=201,
            speed=22.22, heart_rate=202,
            interval=datetime.timedelta(seconds=20.2))]


def test_unpack_track_point_parameter__raises_for_wrong_message_type() -> None:
    parameter = make_track_point_trackhead_pack(
        date=datetime.datetime(2001, 2, 3, 4, 5, 6),
        no_track_points=1, duration=datetime.timedelta(seconds=100.0),
        distance=2, no_laps=3, session_start=4, session_last=5,
        msg_type=0x56)

    with pytest.raises(SQ100MessageException):
        arival_sq100.unpack_track_point_parameter(parameter)


def make_track_list_entry_pack(
        date: datetime.datetime,
        duration: datetime.timedelta,
        no_points: int,
        distance: int,
        no_laps: int,
        memory_block_index: int,
        track_id: int,
) -> bytes:
    return struct.pack(
        ">6B3I5HB",
        date.year - 2000, date.month, date.day,
        date.hour, date.minute, date.second,
        no_points,
        int(round(duration.total_seconds() * 10)),
        distance,
        no_laps,
        0,
        memory_block_index,
        0,
        track_id,
        0)


def test_unpack_track_list_parameter__unpacks_correct_data() -> None:
    parameter = (
        make_track_list_entry_pack(
            date=datetime.datetime(2001, 1, 2, 3, 4, 5),
            duration=datetime.timedelta(seconds=11.1),
            no_points=11,
            distance=12,
            no_laps=13,
            memory_block_index=14,
            track_id=15)
        + make_track_list_entry_pack(
            date=datetime.datetime(2002, 11, 12, 13, 14, 15),
            duration=datetime.timedelta(seconds=22.2),
            no_points=21,
            distance=22,
            no_laps=23,
            memory_block_index=24,
            track_id=25))

    tracks = arival_sq100.unpack_track_list_parameter(parameter)
    assert tracks == [
        arival_sq100.TrackListEntry(
            date=datetime.datetime(2001, 1, 2, 3, 4, 5),
            duration=datetime.timedelta(seconds=11.1),
            no_track_points=11, distance=12, no_laps=13,
            memory_block_index=14, id=15),
        arival_sq100.TrackListEntry(
            date=datetime.datetime(2002, 11, 12, 13, 14, 15),
            duration=datetime.timedelta(seconds=22.2),
            no_track_points=21, distance=22, no_laps=23,
            memory_block_index=24, id=25)]


def make_message_pack(
        command: int,
        parameter: bytes,
        payload_length: int,
        checksum: int) -> bytes:
    return struct.pack(
        ">BH%dsB" % len(parameter), command, payload_length,
        parameter, checksum)


def test_unpack_message__unpacks_correct_data() -> None:
    message_pack = make_message_pack(
        command=123, parameter=b"Hello world",
        payload_length=len("Hello world"),
        checksum=arival_sq100.calc_checksum(b"Hello world"))
    message = arival_sq100.unpack_message(message_pack)
    assert message == arival_sq100.Message(
        command=123, parameter=b"Hello world", payload_length=11,
        checksum=arival_sq100.calc_checksum(b"Hello world"))


def test_unpack_message__raises_if_checksum_is_wrong() -> None:
    message_pack = make_message_pack(
        command=123, parameter=b"Hello world",
        payload_length=len("Hello world"),
        checksum=arival_sq100.calc_checksum(b"Hello world now"))
    with pytest.raises(SQ100MessageException):
        arival_sq100.unpack_message(message_pack)


def test_unpack_message__raises_if_payload_leng_is_wrong() -> None:
    message_pack = make_message_pack(
        command=123, parameter=b"Hello world",
        payload_length=len("Hello world now"),
        checksum=arival_sq100.calc_checksum(b"Hello world"))
    with pytest.raises(SQ100MessageException):
        arival_sq100.unpack_message(message_pack)


def make_track_list_entry(
    date: datetime.datetime = datetime.datetime(1987, 12, 19),
    no_laps: int = 0,
    duration: datetime.timedelta = datetime.timedelta(seconds=0),
    distance: int = 0,
    no_track_points: int = 0,
    memory_block_index: int = 0,
    id: int = 0,
) -> arival_sq100.TrackListEntry:
    return arival_sq100.TrackListEntry(
        date=date, no_laps=no_laps, duration=duration, distance=distance,
        no_track_points=no_track_points, memory_block_index=memory_block_index,
        id=id)


def test_track_ids_to_memory_indices__returns_correct_indices() -> None:
    memory_indices = arival_sq100.track_ids_to_memory_indices(
        tracks=[
            make_track_list_entry(id=1, memory_block_index=10),
            make_track_list_entry(id=2, memory_block_index=20),
            make_track_list_entry(id=3, memory_block_index=30),
            make_track_list_entry(id=4, memory_block_index=40)],
        track_ids=[3, 1, 2])
    assert memory_indices == [30, 10, 20]


def test_query__calls_correct_write(mocker: MockerFixture) -> None:
    mock_connection = mocker.create_autospec(
        serial_connection.SerialConnection)
    mock_connection.read.side_effect = [
        bytes([0, 0, 2]),
        b'hi' + bytes([2 ^ ord('h') ^ ord('i')])]

    arival_sq100.query(
        connection=mock_connection,
        command=42,
        parameter=b"ab")

    mock_connection.write.assert_called_once_with(
        bytes([2, 0, 3, 42]) + b'ab' + bytes([3 ^ 42 ^ ord('a') ^ ord('b')]))


def test_query__returns_correct_message(mocker: MockerFixture) -> None:
    mock_connection = mocker.create_autospec(
        serial_connection.SerialConnection)
    mock_connection.read.side_effect = [
        bytes([0, 0, 2]),
        b'hi' + bytes([2 ^ ord('h') ^ ord('i')])]

    message = arival_sq100.query(
        connection=mock_connection,
        command=42,
        parameter=b"ab")

    assert message.parameter == b'hi'
    assert message.payload_length == 2
