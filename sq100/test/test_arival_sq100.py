import datetime
import mock
import pytest
import struct

from sq100.arival_sq100 import ArivalSQ100
from sq100.exceptions import SQ100MessageException
from sq100.track import Track

"""
private methods
"""


def test_calc_checksum():
    payload = b"\x45\x73\xAF\x20"
    payload_len = struct.pack(">H", len(payload))
    checksum = 0
    checksum ^= payload_len[0]
    checksum ^= payload_len[1]
    for b in payload:
        checksum ^= b
    assert(checksum == ArivalSQ100._calc_checksum(payload))


def test_create_message():
    assert(ArivalSQ100._create_message(0x78) == b'\x02\x00\x01\x78\x79')


def test_get_tracks_message_type():
    msg = mock.MagicMock()
    msg.parameter = bytearray(30)
    msg.parameter[28] = 0x00
    assert ArivalSQ100._get_tracks_message_type(msg) == "track info"
    msg.parameter[28] = 0xAA
    assert ArivalSQ100._get_tracks_message_type(msg) == "lap info"
    msg.parameter[28] = 0x55
    assert ArivalSQ100._get_tracks_message_type(msg) == "track points"
    msg.parameter[28] = 0xAB
    with pytest.raises(SQ100MessageException):
        ArivalSQ100._get_tracks_message_type(msg)


@mock.patch('sq100.arival_sq100.ArivalSQ100._unpack_lap_info_parameter')
def test_process_get_tracks_lap_info_msg(mock_unpack):
    msg = mock.MagicMock()
    msg.parameter = "message parameter"
    track = mock.create_autospec(Track())
    mock_unpack.return_value = ("the trackhead", "the laps")
    track.compatible_to.return_value = True
    ArivalSQ100._process_get_tracks_lap_info_msg(track, msg)
    assert track.laps == "the laps"
    mock_unpack.assert_called_once_with("message parameter")
    track.compatible_to.assert_called_once_with("the trackhead")


@mock.patch('sq100.arival_sq100.ArivalSQ100._unpack_lap_info_parameter')
def test_process_get_tracks_lap_info_msg_incompatible(mock_unpack):
    msg = mock.MagicMock()
    msg.parameter = "message parameter"
    track = mock.create_autospec(Track())
    track.laps = "empty"
    mock_unpack.return_value = ("the trackhead", "the laps")
    track.compatible_to.return_value = False
    with pytest.raises(SQ100MessageException):
        ArivalSQ100._process_get_tracks_lap_info_msg(track, msg)
    assert track.laps == "empty"
    mock_unpack.assert_called_once_with("message parameter")
    track.compatible_to.assert_called_once_with("the trackhead")


@mock.patch('sq100.arival_sq100.ArivalSQ100._unpack_track_info_parameter')
def test_process_get_tracks_track_info_msg(mock_unpack):
    msg = mock.MagicMock()
    msg.parameter = "message parameter"
    mock_unpack.return_value = ("the track")
    track = ArivalSQ100._process_get_tracks_track_info_msg(msg)
    assert track == "the track"
    mock_unpack.assert_called_once_with("message parameter")


def test_unpack_lap_info_parameter():
    date = datetime.datetime(2016, 7, 23, 14, 30, 11)
    no_track_points = 1230
    duration = datetime.timedelta(seconds=2345.5)
    distance = 4321  # meter
    no_laps = 2

    lap_1_duration = datetime.timedelta(seconds=3456.7)
    lap_1_total_time = datetime.timedelta(seconds=3456.7)
    lap_1_distance = 3589
    lap_1_calories = 111
    lap_1_max_speed = 312
    lap_1_max_heart_rate = 198
    lap_1_avg_heart_rate = 120
    lap_1_min_height = 345
    lap_1_max_height = 810
    lap_1_first_index = 0
    lap_1_last_index = 612

    lap_2_duration = datetime.timedelta(seconds=1122.2)
    lap_2_total_time = datetime.timedelta(seconds=8899.4)
    lap_2_distance = 657
    lap_2_calories = 854
    lap_2_max_speed = 64
    lap_2_max_heart_rate = 205
    lap_2_avg_heart_rate = 167
    lap_2_min_height = 889
    lap_2_max_height = 673
    lap_2_first_index = 613
    lap_2_last_index = 1229

    parameter = (
        struct.pack(
            ">6B3IH8sB",
            date.year - 2000, date.month, date.day,
            date.hour, date.minute, date.second,
            no_track_points,
            round(duration.total_seconds() * 10), distance,
            no_laps, b'', 0xAA) +
        struct.pack(
            ">3I3H2B2H13s2H",
            round(lap_1_duration.total_seconds() * 10),
            round(lap_1_total_time.total_seconds() * 10),
            lap_1_distance, lap_1_calories,
            0, lap_1_max_speed, lap_1_max_heart_rate, lap_1_avg_heart_rate,
            lap_1_min_height, lap_1_max_height, b'',
            lap_1_first_index, lap_1_last_index) +
        struct.pack(
            ">3I3H2B2H13s2H",
            round(lap_2_duration.total_seconds() * 10),
            round(lap_2_total_time.total_seconds() * 10),
            lap_2_distance, lap_2_calories, 0,
            lap_2_max_speed, lap_2_max_heart_rate, lap_2_avg_heart_rate,
            lap_2_min_height, lap_2_max_height, b'',
            lap_2_first_index, lap_2_last_index)
    )

    print(len(parameter))

    track, laps = ArivalSQ100._unpack_lap_info_parameter(parameter)

    assert(track.date == date)
    assert(track.no_track_points == no_track_points)
    assert(track.duration == duration)
    assert(track.distance == distance)
    assert(track.no_laps == no_laps)

    assert(laps[0].duration == lap_1_duration)
    assert(laps[0].total_time == lap_1_total_time)
    assert(laps[0].distance == lap_1_distance)
    assert(laps[0].calories == lap_1_calories)
    assert(laps[0].max_speed == lap_1_max_speed)
    assert(laps[0].max_heart_rate == lap_1_max_heart_rate)
    assert(laps[0].avg_heart_rate == lap_1_avg_heart_rate)
    assert(laps[0].min_height == lap_1_min_height)
    assert(laps[0].max_height == lap_1_max_height)
    assert(laps[0].first_index == lap_1_first_index)
    assert(laps[0].last_index == lap_1_last_index)

    assert(laps[1].duration == lap_2_duration)
    assert(laps[1].total_time == lap_2_total_time)
    assert(laps[1].distance == lap_2_distance)
    assert(laps[1].calories == lap_2_calories)
    assert(laps[1].max_speed == lap_2_max_speed)
    assert(laps[1].max_heart_rate == lap_2_max_heart_rate)
    assert(laps[1].avg_heart_rate == lap_2_avg_heart_rate)
    assert(laps[1].min_height == lap_2_min_height)
    assert(laps[1].max_height == lap_2_max_height)
    assert(laps[1].first_index == lap_2_first_index)
    assert(laps[1].last_index == lap_2_last_index)


def test_unpack_message():
    command = 123
    parameter = b"Hello world"
    payload_length = len(parameter)
    checksum = ArivalSQ100._calc_checksum(parameter)
    message = struct.pack(">BH%dsB" % len(parameter), command, payload_length,
                          parameter, checksum)
    data = ArivalSQ100._unpack_message(message)
    assert(data.command == command)
    assert(data.parameter == parameter)
    assert(data.payload_length == payload_length)
    assert(data.checksum == checksum)


def test_unpack_track_info_parameter():
    date = datetime.datetime(2016, 7, 23, 14, 30, 11)
    no_track_points = 1230
    duration = datetime.timedelta(seconds=2345.9)
    distance = 4321
    no_laps = 3
    memory_block_index = 51
    track_id = 13
    calories = 714
    max_speed = 89
    max_heart_rate = 198
    avg_heart_rate = 153
    asc_height = 873
    des_height = 543
    min_height = 345
    max_height = 1122

    parameter = struct.pack(
        ">6B3I5HB3H2B4H13s",
        date.year - 2000, date.month, date.day,
        date.hour, date.minute, date.second,
        no_track_points,
        round(duration.total_seconds() * 10),
        distance,
        no_laps, 0, memory_block_index, 0, track_id,
        0,
        calories, 0, max_speed,
        max_heart_rate, avg_heart_rate,
        asc_height, des_height, min_height, max_height,
        b'')

    track = ArivalSQ100._unpack_track_info_parameter(parameter)
    assert(track.date == date)
    assert(track.no_track_points == no_track_points)
    assert(track.duration == duration)
    assert(track.distance == distance)
    assert(track.no_laps == no_laps)
    assert(track.memory_block_index == memory_block_index)
    assert(track.id == track_id)
    assert(track.calories == calories)
    assert(track.max_speed == max_speed)
    assert(track.max_heart_rate == max_heart_rate)
    assert(track.avg_heart_rate == avg_heart_rate)
    assert(track.ascending_height == asc_height)
    assert(track.descending_height == des_height)
    assert(track.min_height == min_height)
    assert(track.max_height == max_height)


def test_unpack_track_list_parameter():
    track_0_date = datetime.datetime(2016, 7, 23, 14, 30, 11)
    track_0_no_points = 1230
    track_0_duration = datetime.timedelta(seconds=465.1)
    track_0_distance = 1281  # meter
    track_0_no_laps = 4
    track_0_memory_block_index = 45
    track_0_id = 5

    track_1_date = datetime.datetime(2016, 7, 23, 14, 30, 11)
    track_1_no_points = 1230
    track_1_duration = datetime.timedelta(seconds=465.1)
    track_1_distance = 1281  # meter
    track_1_no_laps = 4
    track_1_memory_block_index = 45
    track_1_id = 5

    parameter = (
        struct.pack(
            ">6B3I5HB",
            track_0_date.year - 2000, track_0_date.month, track_0_date.day,
            track_0_date.hour, track_0_date.minute, track_0_date.second,
            track_0_no_points,
            int(round(track_0_duration.total_seconds() * 10)),
            track_0_distance,
            track_0_no_laps,
            0,
            track_0_memory_block_index,
            0,
            track_0_id,
            0) +
        struct.pack(
            ">6B3I5HB",
            track_1_date.year - 2000, track_1_date.month, track_1_date.day,
            track_1_date.hour, track_1_date.minute, track_1_date.second,
            track_1_no_points,
            int(round(track_1_duration.total_seconds() * 10)),
            track_1_distance,
            track_1_no_laps,
            0,
            track_1_memory_block_index,
            0,
            track_1_id,
            0))

    tracks = ArivalSQ100._unpack_track_list_parameter(parameter)

    assert(tracks[0].date == track_0_date)
    assert(tracks[0].no_track_points == track_0_no_points)
    assert(tracks[0].duration == track_0_duration)
    assert(tracks[0].distance == track_0_distance)
    assert(tracks[0].no_laps == track_0_no_laps)
    assert(tracks[0].memory_block_index == track_0_memory_block_index)
    assert(tracks[0].id == track_0_id)

    assert(tracks[1].date == track_1_date)
    assert(tracks[1].no_track_points == track_1_no_points)
    assert(tracks[1].duration == track_1_duration)
    assert(tracks[1].distance == track_1_distance)
    assert(tracks[1].no_laps == track_1_no_laps)
    assert(tracks[1].memory_block_index == track_1_memory_block_index)
    assert(tracks[1].id == track_1_id)


def test_unpack_track_point_parameter():
    track_date = datetime.datetime(2016, 7, 23, 14, 30, 11)
    track_no_track_points = 1230
    track_duration = datetime.timedelta(seconds=2345.2)
    track_distance = 4321  # meter
    track_no_laps = 2
    session_start = 120
    session_last = 121

    tp_0_latitude = 51.532719  # degree
    tp_0_longitude = 9.935127  # degree
    tp_0_altitude = 156  # meter
    tp_0_speed = 10.2  # km/h
    tp_0_heart_rate = 142
    tp_0_interval = datetime.timedelta(seconds=1.3)

    tp_1_latitude = -22.906846  # degree
    tp_1_longitude = -43.172896  # degree
    tp_1_altitude = 32  # meter
    tp_1_speed = 14.9  # km/h
    tp_1_heart_rate = 168
    tp_1_interval = datetime.timedelta(seconds=5.1)

    parameter = (
        struct.pack(
            ">6B3IH2IB",
            track_date.year - 2000, track_date.month, track_date.day,
            track_date.hour, track_date.minute, track_date.second,
            track_no_track_points,
            round(track_duration.total_seconds() * 10),
            track_distance,
            track_no_laps, session_start, session_last, 0x55) +
        struct.pack(
            ">2i3HB2H6s",
            int(round(tp_0_latitude * 1e6)),
            int(round(tp_0_longitude * 1e6)),
            tp_0_altitude,
            0,
            int(round(tp_0_speed * 100)),
            tp_0_heart_rate,
            0,
            int(round(tp_0_interval.total_seconds() * 10)),
            b'') +
        struct.pack(
            ">2i3HB2H6s",
            int(round(tp_1_latitude * 1e6)),
            int(round(tp_1_longitude * 1e6)),
            tp_1_altitude, 0,
            int(round(tp_1_speed * 100)),
            tp_1_heart_rate,
            0,
            int(round(tp_1_interval.total_seconds() * 10)),
            b''))

    track, session, track_points = ArivalSQ100._unpack_track_point_parameter(
        parameter)

    assert(track.date == track_date)
    assert(track.no_track_points == track_no_track_points)
    assert(track.duration == track_duration)
    assert(track.distance == track_distance)
    assert(track.no_laps == track_no_laps)

    assert(session[0] == session_start)
    assert(session[1] == session_last)

    assert(track_points[0].latitude == tp_0_latitude)
    assert(track_points[0].longitude == tp_0_longitude)
    assert(track_points[0].altitude == tp_0_altitude)
    assert(track_points[0].speed == tp_0_speed)
    assert(track_points[0].heart_rate == tp_0_heart_rate)
    assert(track_points[0].interval == tp_0_interval)

    assert(track_points[1].latitude == tp_1_latitude)
    assert(track_points[1].longitude == tp_1_longitude)
    assert(track_points[1].altitude == tp_1_altitude)
    assert(track_points[1].speed == tp_1_speed)
    assert(track_points[1].heart_rate == tp_1_heart_rate)
    assert(track_points[1].interval == tp_1_interval)
