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
from sq100.test.dummies import make_track, make_track_point
import sq100.utilities as utils


def test_calc_tracks_bounds() -> None:
    tracks = [
        make_track(track_points=[
            make_track_point(latitude=-20., longitude=2.),
            make_track_point(latitude=-5., longitude=11.),
        ]),
        make_track(track_points=[
            make_track_point(latitude=5., longitude=-3.),
            make_track_point(latitude=12., longitude=10.),
        ]),
    ]
    bounds = utils.calc_tracks_bounds(tracks)
    expected = CoordinateBounds(min=Point(-20, -3), max=Point(12, 11))
    assert bounds == expected
