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
from mock import create_autospec, patch
from typing import Any
import xml.etree.ElementTree as etree

import sq100.gpx as gpx
from sq100.data_types import CoordinateBounds, Point, Track, TrackPoint
from sq100.test.dummies import make_track_info, make_tracks, make_track_point


def test_create_bounds_element() -> None:
    bounds = CoordinateBounds(
        min=Point(latitude=10.8, longitude=-8.1),
        max=Point(latitude=25.0, longitude=-2.9))
    elem = gpx._create_bounds_element(value=bounds)
    assert float(elem.get("minlat", "0")) == bounds.min.latitude
    assert float(elem.get("minlon", "0")) == bounds.min.longitude
    assert float(elem.get("maxlat", "0")) == bounds.max.latitude
    assert float(elem.get("maxlon", "0")) == bounds.max.longitude


def test_create_datetime_element_with_tzinfo() -> None:
    dt = datetime.datetime(
        year=1987, month=12, day=19, hour=15, minute=30, second=20,
        tzinfo=datetime.timezone(datetime.timedelta(hours=1)))
    elem = gpx._create_datetime_element(ns="timo", tag="birth", value=dt)
    assert elem.tag == "{timo}birth"
    assert elem.text == "1987-12-19T14:30:20Z"


def test_create_datetime_element_without_tzinfo() -> None:
    dt = datetime.datetime(
        year=1987, month=12, day=19, hour=15, minute=30, second=20)
    elem = gpx._create_datetime_element(ns="timo", tag="birth", value=dt)
    assert elem.tag == "{timo}birth"
    assert elem.text == "1987-12-19T15:30:20Z"


def test_create_decimal_element() -> None:
    elem = gpx._create_decimal_element(ns="timo", tag="number", value=-42.5)
    assert elem.tag == '{timo}number'
    assert elem.text is not None
    assert float(elem.text) == -42.5


def test_create_garmin_track_point_extension_element() -> None:
    track_point = create_autospec(TrackPoint)
    track_point.heart_rate = 150
    ns = 'http://www.garmin.com/xmlschemas/TrackPointExtension/v2'
    elem = gpx._create_garmin_track_point_extension_element(track_point)
    heart_rate_element = elem.find('{%s}hr' % ns)
    assert elem.tag == ("{%s}TrackPointExtension" % ns)
    assert heart_rate_element is not None
    assert heart_rate_element.text is not None
    assert int(heart_rate_element.text) == 150


def test_create_gpx_element() -> None:
    tracks = make_tracks(num=2)
    elem = gpx._create_gpx_element(tracks)
    ns = '{%s}' % gpx.gpx_ns
    assert elem.tag == 'gpx'
    gpx_tracks = elem.findall(ns + 'trk')
    assert len(gpx_tracks) == 2
    gpx_number_0 = gpx_tracks[0].find(ns + 'number')
    gpx_number_1 = gpx_tracks[1].find(ns + 'number')
    assert gpx_number_0 is not None
    assert gpx_number_1 is not None
    assert gpx_number_0.text == '0'
    assert gpx_number_1.text == '1'
    # assert len(elem.findall(ns + 'metadata')) == 1


def test_create_metadata_element() -> None:
    elem = gpx._create_metadata_element(
        bounds=CoordinateBounds(min=Point(1., 2.), max=Point(3., 4.)),
        date=datetime.datetime(1987, 12, 19, 15, 30, 12),
        name="my name",
        description="my metadata description",
        ns="timo")
    name_element = elem.find('{timo}name')
    desc_element = elem.find('{timo}desc')
    time_element = elem.find('{timo}time')
    bounds_element = elem.find('{timo}bounds')
    assert name_element is not None
    assert desc_element is not None
    assert time_element is not None
    assert bounds_element is not None
    assert name_element.text == "my name"
    assert desc_element.text == "my metadata description"
    assert time_element.text == '1987-12-19T15:30:12Z'
    assert bounds_element.get("minlat") == "1.0"
    assert bounds_element.get("minlon") == "2.0"
    assert bounds_element.get("maxlat") == "3.0"
    assert bounds_element.get("maxlon") == "4.0"


def test_create_string_element() -> None:
    elem = gpx._create_string_element(ns="timo", tag="name", value="nachstedt")
    assert elem.tag == "{timo}name"
    assert elem.text == "nachstedt"


def test_create_track_element() -> None:
    ns = '{%s}' % gpx.gpx_ns
    track = Track(
        info=make_track_info(id=5),
        laps=[],
        track_points=[],
    )
    src = "My heart rate computer"
    number = 10
    elem = gpx._create_track_element(track=track, number=number, src=src)
    # assert elem.find(ns + 'cmt').text == "id=5"
    # assert elem.find(ns + 'src').text == "My heart rate computer"
    assert elem.find(ns + 'trkseg') is not None


@patch('sq100.gpx._create_track_point_extensions_element', autospec=True)
def test_create_track_point_element(mock_create_extensions_elem: Any) -> None:
    ns = '{%s}' % gpx.gpx_ns
    mock_create_extensions_elem.return_value = etree.Element(ns + 'extensions')
    tp = make_track_point(
        latitude=23.4, longitude=-32.1, altitude=678.51,
        # date=datetime.datetime(1987, 12, 19, 15, 30, 20),
    )
    elem = gpx._create_track_point_element(tp)
    # assert float(elem.get('lat')) == tp.latitude
    # assert float(elem.get('lon')) == tp.longitude
    # assert float(elem.find(ns + 'ele').text) == tp.altitude
    # assert elem.find(ns + 'time').text == '1987-12-19T15:30:20Z'
    assert elem.find(ns + 'extensions') is not None


def test_create_track_point_extensions_element() -> None:
    track_point = make_track_point()
    elem = gpx._create_track_point_extensions_element(track_point)
    assert elem.tag == "{%s}%s" % (gpx.gpx_ns, 'extensions')
    garmin = '{%s}%s' % (gpx.tpex_ns, 'TrackPointExtension')
    assert elem.find(garmin) is not None


def test_create_track_segment_element() -> None:
    track_points = [
        make_track_point(latitude=1),
        make_track_point(latitude=2),
        make_track_point(latitude=3)]
    elem = gpx._create_track_segment_element(track_points)
    assert elem.tag == "{%s}%s" % (gpx.gpx_ns, 'trkseg')
    trkpt = '{' + gpx.gpx_ns + '}trkpt'
    assert elem.findall(trkpt)[0].get('lat') == "1"
    assert elem.findall(trkpt)[1].get('lat') == "2"
    assert elem.findall(trkpt)[2].get('lat') == "3"


def test_indent() -> None:
    elem = etree.Element('main')
    etree.SubElement(elem, "suba")
    gpx._indent(elem)
    expected = "<main>\n  <suba />\n</main>\n"
    actual = etree.tostring(elem, encoding='unicode')
    assert actual == expected


@ patch('sq100.gpx.etree.ElementTree', autospec=True)
@ patch('sq100.gpx._create_gpx_element', autospec=True)
def test_tracks_to_gpx(
        mock_create_gpx_element: Any,
        mock_element_tree: Any) -> None:
    tracks = make_tracks(num=2)
    filename = 'tmp.gpx'
    mock_create_gpx_element.return_value = etree.Element("gpx")
    mock_doc = mock_element_tree.return_value
    gpx.tracks_to_gpx(tracks, filename)
    mock_doc.write.assert_called_once()
    assert mock_doc.write.call_args[0][0] == "tmp.gpx"
