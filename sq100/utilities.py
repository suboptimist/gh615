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

from sq100.data_types import CoordinateBounds, Point

from typing import Set


def calc_tracks_bounds(tracks):
    track_bounds = [t.bounds() for t in tracks]
    min_latitude = min([b.min.latitude for b in track_bounds])
    min_longitude = min([b.min.longitude for b in track_bounds])
    max_latitude = max([b.max.latitude for b in track_bounds])
    max_longitude = max([b.max.longitude for b in track_bounds])
    return CoordinateBounds(
        minimum=Point(latitude=min_latitude, longitude=min_longitude),
        maximum=Point(latitude=max_latitude, longitude=max_longitude))


def parse_range(astr):
    result: Set[int] = set()
    for part in astr.split(','):
        x = part.split('-')
        result.update(range(int(x[0]), int(x[-1]) + 1))
    return sorted(result)
