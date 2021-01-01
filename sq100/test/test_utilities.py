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

from mock import create_autospec

from sq100.data_types import CoordinateBounds, Point, Track
import sq100.utilities as utils


def test_calc_tracks_bounds():
    tracks = [create_autospec(Track) for _ in range(3)]
    track_bounds = [
        CoordinateBounds(min=Point(-20, 5), max=Point(0, 11)),
        CoordinateBounds(min=Point(8, -3), max=Point(10, 2)),
        CoordinateBounds(min=Point(5, 7), max=Point(12, 9))]
    for i in range(3):
        tracks[i].bounds.return_value = track_bounds[i]
    bounds = utils.calc_tracks_bounds(tracks)
    expected = CoordinateBounds(min=Point(-20, -3), max=Point(12, 11))
    print(bounds)
    print(expected)
    assert bounds == expected
