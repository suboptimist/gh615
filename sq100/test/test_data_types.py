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

import copy
import datetime

from sq100.data_types import Track


def test_track_compare_to():
    t1 = Track(ascending_height=75,
               avg_heart_rate=154,
               calories=891,
               date=datetime.datetime(2016, 7, 23, 14, 30, 15),
               descending_height=410,
               distance=8914,
               duration=datetime.timedelta(seconds=8793.2),
               max_heart_rate=212,
               max_height=500,
               max_speed=14,
               memory_block_index=12,
               min_height=12,
               no_laps=4,
               no_track_points=20,
               id=2)

    t2 = copy.copy(t1)
    assert(t1.compatible_to(t2) is True)
    assert(t2.compatible_to(t1) is True)

    t2 = Track()
    assert(t1.compatible_to(t2) is True)
    assert(t2.compatible_to(t1) is True)

    t2 = copy.copy(t1)
    t2.calories += 1
    assert(t1.compatible_to(t2) is False)
    assert(t2.compatible_to(t1) is False)

    t2 = Track(date=t1.date, duration=t1.duration, no_laps=t1.no_laps)
    assert(t1.compatible_to(t2) is True)
    assert(t2.compatible_to(t1) is True)

    t2.max_heart_rate = t1.max_heart_rate - 1
    assert(t1.compatible_to(t2) is False)
    assert(t2.compatible_to(t1) is False)
