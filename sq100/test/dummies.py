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
from typing import List, Optional, TypedDict

from sq100 import arival_sq100


class TrackPointOptins(TypedDict, total=False):
    latitude: float
    longitude: float
    altitude: float
    interval: datetime.timedelta
    speed: float
    heart_rate: float


def make_track_points(args: List[TrackPointOptins]) -> List[arival_sq100.TrackPoint]:
    return [make_track_point(**kwargs) for kwargs in args]


def make_track_point(
    latitude: float = 0,
    longitude: float = 0,
    altitude: float = 0,
    interval: datetime.timedelta = datetime.timedelta(0),
    speed: float = 0,
    heart_rate: float = 0,
) -> arival_sq100.TrackPoint:
    return arival_sq100.TrackPoint(
        latitude=latitude,
        longitude=longitude,
        altitude=altitude,
        interval=interval,
        speed=speed,
        heart_rate=heart_rate,
    )


def make_track_info(
    date: datetime.datetime = datetime.datetime.now(),
    distance: float = 0,
    duration: datetime.timedelta = datetime.timedelta(0),
    id: int = 0,
    no_laps: int = 0,
    no_track_points: int = 0,
    ascending_height: int = 0,
    avg_heart_rate: float = 0,
    calories: float = 0,
    descending_height: float = 0,
    max_heart_rate: float = 0,
    max_height: float = 0,
    max_speed: float = 0,
    memory_block_index: int = 0,
    min_height: float = 0,
) -> arival_sq100.TrackInfo:
    return arival_sq100.TrackInfo(
        date=date,
        distance=distance,
        duration=duration,
        id=id,
        no_laps=no_laps,
        no_track_points=no_track_points,
        ascending_height=ascending_height,
        avg_heart_rate=avg_heart_rate,
        calories=calories,
        descending_height=descending_height,
        max_heart_rate=max_heart_rate,
        max_height=max_height,
        max_speed=max_speed,
        memory_block_index=memory_block_index,
        min_height=min_height,
    )


def make_track(
    track_points: Optional[List[arival_sq100.TrackPoint]] = None,
) -> arival_sq100.Track:
    if track_points is None:
        track_points = []
    return arival_sq100.Track(
        info=make_track_info(), laps=[], track_points=track_points
    )


def make_tracks(num: int = 0) -> List[arival_sq100.Track]:
    return [make_track() for _ in range(num)]
