import datetime
import mock
import struct

from sq100.arival_sq100 import ArivalSQ100


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
    duration = datetime.timedelta(seconds=2345)
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
        no_track_points, duration.seconds * 10, distance,
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


def test_unpack_lap_info_parameter():
    date = datetime.datetime(2016, 7, 23, 14, 30, 11)
    no_track_points = 1230
    duration = datetime.timedelta(seconds=2345)
    distance = 4321
    no_laps = 2

    lap_1_duration = datetime.timedelta(seconds=3456)
    lap_1_total_time = datetime.timedelta(seconds=3456)
    lap_1_distance = 3589
    lap_1_calories = 111
    lap_1_max_speed = 312
    lap_1_max_heart_rate = 198
    lap_1_avg_heart_rate = 120
    lap_1_min_height = 345
    lap_1_max_height = 810
    lap_1_first_index = 0
    lap_1_last_index = 612

    lap_2_duration = datetime.timedelta(seconds=1122)
    lap_2_total_time = datetime.timedelta(seconds=8899)
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
            no_track_points, duration.seconds * 10, distance,
            no_laps, b'', 0xAA) +
        struct.pack(
            ">3I3H2B2H13s2H",
            lap_1_duration.seconds * 10, lap_1_total_time.seconds * 10,
            lap_1_distance, lap_1_calories,
            0, lap_1_max_speed, lap_1_max_heart_rate, lap_1_avg_heart_rate,
            lap_1_min_height, lap_1_max_height, b'',
            lap_1_first_index, lap_1_last_index) +
        struct.pack(
            ">3I3H2B2H13s2H",
            lap_2_duration.seconds * 10, lap_2_total_time.seconds * 10,
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
