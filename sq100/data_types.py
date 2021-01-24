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

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Track:
    info: TrackInfo
    laps: List[Lap]
    track_points: List[TrackPoint]


@dataclass
class TrackInfo:
    date: datetime.datetime
    distance: float
    duration: datetime.timedelta
    no_laps: int
    no_track_points: int
    ascending_height: float
    avg_heart_rate: float
    calories: float
    descending_height: float
    id: int
    max_heart_rate: float
    max_height: float
    max_speed: float
    memory_block_index: int
    min_height: float


@dataclass
class Lap:
    duration: datetime.timedelta
    total_time: datetime.timedelta
    distance: float
    calories: float
    max_speed: float
    max_heart_rate: float
    avg_heart_rate: float
    min_height: float
    max_height: float
    first_index: int
    last_index: int


@dataclass
class TrackPoint:
    latitude: float
    longitude: float
    altitude: float
    interval: datetime.timedelta
    speed: float
    heart_rate: float


@dataclass
class CoordinateBounds:
    min: Point
    max: Point


@dataclass
class Point:
    latitude: float
    longitude: float

    # def bounds(self) -> Optional[CoordinateBounds]:
    #     if len(self.track_points) == 0:
    #         return None
    #     return CoordinateBounds(
    #         min=Point(
    #             latitude=min(t.latitude for t in self.track_points),
    #             longitude=min(t.longitude for t in self.track_points)),
    #         max=Point(
    #             latitude=max(t.latitude for t in self.track_points),
    #             longitude=max(t.longitude for t in self.track_points)))
