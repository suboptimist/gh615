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


class CoordinateBounds(object):

    def __init__(self, minimum, maximum):
        self.min = minimum
        self.max = maximum

    def __str__(self):
        return "(%s, %s)" % (self.min, self.max)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class Lap(object):

    def __init__(self,
                 duration=None,
                 total_time=None,
                 distance=None,
                 calories=None,
                 max_speed=None,
                 max_heart_rate=None,
                 avg_heart_rate=None,
                 min_height=None,
                 max_height=None,
                 first_index=None,
                 last_index=None):
        self.duration = duration
        self.total_time = total_time
        self.distance = distance
        self.calories = calories
        self.max_speed = max_speed
        self.max_heart_rate = max_heart_rate
        self.avg_heart_rate = avg_heart_rate
        self.min_height = min_height
        self.max_height = max_height
        self.first_index = first_index
        self.last_index = last_index

#     def calculateDate(self, date):
#         self.end = date + datetime.timedelta(
#             milliseconds = (self.__until * 100))
#         self.start = self.end - datetime.timedelta(
#             milliseconds = (self.__elapsed * 100))
#         self.duration = self.end - self.start
#
#     def calculateCoordinates(self, trackpoints):
#         relative_to_start = relative_to_end = {}
#
#         for trackpoint in trackpoints:
#             relative_to_start[abs(self.start - trackpoint.date)] = trackpoint
#             relative_to_end[abs(self.end - trackpoint.date)] = trackpoint
#
#         nearest_start_point = relative_to_start[min(relative_to_start)]
#         nearest_end_point = relative_to_end[min(relative_to_end)]
#
#         self.startPoint = Point(nearest_start_point.latitude,
#                                 nearest_start_point.longitude)
#         self.endPoint = Point(nearest_end_point.latitude,
#                               nearest_end_point.longitude)


class Point(object):

    def __init__(self, latitude=None, longitude=None):
        self.latitude = latitude
        self.longitude = longitude

    def __str__(self):
        return "(%s, %s)" % (self.latitude, self.longitude)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class Track(object):

    def __init__(self,
                 ascending_height=None,
                 avg_heart_rate=None,
                 calories=None,
                 date=None,
                 descending_height=None,
                 description=None,
                 distance=None,
                 duration=None,
                 laps=None,
                 max_heart_rate=None,
                 max_height=None,
                 max_speed=None,
                 memory_block_index=None,
                 min_height=None,
                 name=None,
                 no_laps=None,
                 no_track_points=None,
                 track_id=None,
                 track_points=None
                 ):
        self.ascending_height = ascending_height
        self.avg_heart_rate = avg_heart_rate
        self.calories = calories
        self.date = date
        self.descending_height = descending_height
        self.description = description
        self.distance = distance
        self.duration = duration
        self.id = track_id
        self.max_heart_rate = max_heart_rate
        self.max_height = max_height
        self.max_speed = max_speed
        self.memory_block_index = memory_block_index
        self.min_height = min_height
        self.name = name
        self.no_laps = no_laps
        self.no_track_points = no_track_points
        self.track_points = track_points if track_points is not None else []
        self.laps = laps if laps is not None else []

    def __str__(self):
        props = ["%s: %s" % ((k, "%d items" % len(v)) if type(v) is list
                             else (k, v))
                 for k, v in self.__dict__.items()
                 if v is not None]
        return "Track(" + ', '.join(sorted(props)) + ")"

    def bounds(self):
        return CoordinateBounds(
            minimum=Point(
                latitude=min(t.latitude for t in self.track_points),
                longitude=min(t.longitude for t in self.track_points)),
            maximum=Point(
                latitude=max(t.latitude for t in self.track_points),
                longitude=max(t.longitude for t in self.track_points)))

    def compatible_to(self, other):
        def c(a, b):
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

    def complete(self):
        return len(self.track_points) == self.no_track_points

    def update_track_point_times(self):
        interval = datetime.timedelta(0)
        for tp in self.track_points:
            interval += tp.interval
            tp.date = self.date + interval


class TrackPoint(Point):

    def __init__(self,
                 latitude=None,
                 longitude=None,
                 altitude=None,
                 speed=None,
                 heart_rate=None,
                 interval=None,
                 date=None):
        Point.__init__(self, latitude=latitude, longitude=longitude)
        self.altitude = altitude
        self.speed = speed
        self.heart_rate = heart_rate
        self.interval = interval
        self.date = date
        Point.__init__(self, latitude, longitude)


class Waypoint(Point):
    TYPES = {
        0: 'DOT',
        1: 'HOUSE',
        2: 'TRIANGLE',
        3: 'TUNNEL',
        4: 'CROSS',
        5: 'FISH',
        6: 'LIGHT',
        7: 'CAR',
        8: 'COMM',
        9: 'REDCROSS',
        10: 'TREE',
        11: 'BUS',
        12: 'COPCAR',
        13: 'TREES',
        14: 'RESTAURANT',
        15: 'SEVEN',
        16: 'PARKING',
        17: 'REPAIRS',
        18: 'MAIL',
        19: 'DOLLAR',
        20: 'GOVOFFICE',
        21: 'CHURCH',
        22: 'GROCERY',
        23: 'HEART',
        24: 'BOOK',
        25: 'GAS',
        26: 'GRILL',
        27: 'LOOKOUT',
        28: 'FLAG',
        29: 'PLANE',
        30: 'BIRD',
        31: 'DAWN',
        32: 'RESTROOM',
        33: 'WTF',
        34: 'MANTARAY',
        35: 'INFORMATION',
        36: 'BLANK'
    }

    def __init__(self, latitude=0, longitude=0, altitude=0, title='', type=0):
        self.altitude = altitude
        self.title = title
        self.type = type
        super(Waypoint, self).__init__(latitude, longitude)

    def __str__(self):
        return "%s (%f,%f)" % (self.title, self.latitude, self.longitude)
