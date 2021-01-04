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
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Any


@dataclass
class Point:
    latitude: float
    longitude: float


@dataclass
class CoordinateBounds:
    min: Point
    max: Point


@dataclass
class Lap:
    duration: datetime.timedelta = None
    total_time: datetime.timedelta = None
    distance: float = None
    calories: float = None
    max_speed: float = None
    max_heart_rate: float = None
    avg_heart_rate: float = None
    min_height: float = None
    max_height: float = None
    first_index: int = None
    last_index: int = None


@dataclass
class TrackPoint:
    latitude: float = None
    longitude: float = None
    altitude: float = None
    interval: datetime.timedelta = None
    speed: float = None
    heart_rate: float = None
    date: datetime.datetime = None


@ dataclass
class Track:
    ascending_height: float = None
    avg_heart_rate: float = None
    calories: float = None
    date: datetime.datetime = None
    descending_height: float = None
    description: str = None
    distance: float = None
    duration: datetime.timedelta = None
    id: int = None
    laps: List[Lap] = None
    max_heart_rate: float = None
    max_height: float = None
    max_speed: float = None
    memory_block_index: int = None
    min_height: float = None
    name: str = None
    no_laps: int = None
    no_track_points: int = None
    track_id: int = None
    track_points: List[TrackPoint] = field(default_factory=list)

    def bounds(self) -> CoordinateBounds:
        return CoordinateBounds(
            min=Point(
                latitude=min(t.latitude for t in self.track_points),
                longitude=min(t.longitude for t in self.track_points)),
            max=Point(
                latitude=max(t.latitude for t in self.track_points),
                longitude=max(t.longitude for t in self.track_points)))

    def compatible_to(self, other: Track) -> bool:
        def c(a: Any, b: Any) -> bool:
            return a is None or b is None or a == b
        return (
            c(self.ascending_height, other.ascending_height)
            and c(self.avg_heart_rate, other.avg_heart_rate)
            and c(self.calories, other.calories)
            and c(self.date, other.date)
            and c(self.descending_height, other.descending_height)
            and c(self.distance, other.distance)
            and c(self.duration, other.duration)
            and c(self.id, other.id)
            and c(self.max_heart_rate, other.max_heart_rate)
            and c(self.max_height, other.max_height)
            and c(self.max_speed, other.max_speed)
            and c(self.memory_block_index, other.memory_block_index)
            and c(self.min_height, other.min_height)
            and c(self.no_laps, other.no_laps)
            and c(self.no_track_points, other.no_track_points))

    def complete(self) -> bool:
        return len(self.track_points) == self.no_track_points

    def update_track_point_times(self) -> None:
        interval = datetime.timedelta(0)
        for tp in self.track_points:
            interval += tp.interval
            tp.date = self.date + interval


class WaypointType(Enum):
    DOT = 0
    HOUSE = 1
    TRIANGLE = 2
    TUNNEL = 3
    CROSS = 4
    FISH = 5
    LIGHT = 6
    CAR = 7
    COMM = 8
    REDCROSS = 9
    TREE = 10
    BUS = 11
    COPCAR = 12
    TREES = 13
    RESTAURANT = 14
    SEVEN = 15
    PARKING = 16
    REPAIRS = 17
    MAIL = 18
    DOLLAR = 19
    GOVOFFICE = 20
    CHURCH = 21
    GROCERY = 22
    HEART = 23
    BOOK = 24
    GAS = 25
    GRILL = 26
    LOOKOUT = 27
    FLAG = 28
    PLANE = 29
    BIRD = 30
    DAWN = 31
    RESTROOM = 32
    WTF = 33
    MANTARAY = 34
    INFORMATION = 35
    BLANK = 36


@ dataclass
class Waypoint(Point):
    latitude: float
    longitude: float
    altitude: float
    title: str
    type: WaypointType
