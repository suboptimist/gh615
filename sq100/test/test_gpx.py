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
import xml.etree.ElementTree as etree

import sq100.gpx as gpx
from sq100.data_types import CoordinateBounds, Point, Track, TrackPoint


def test_create_bounds_element():
    bounds = CoordinateBounds(
        min=Point(latitude=10.8, longitude=-8.1),
        max=Point(latitude=25.0, longitude=-2.9))
    elem = gpx._create_bounds_element(value=bounds)
    assert float(elem.get("minlat")) == bounds.min.latitude
    assert float(elem.get("minlon")) == bounds.min.longitude
    assert float(elem.get("maxlat")) == bounds.max.latitude
    assert float(elem.get("maxlon")) == bounds.max.longitude


def test_create_datetime_element_with_tzinfo():
    dt = datetime.datetime(
        year=1987, month=12, day=19, hour=15, minute=30, second=20,
        tzinfo=datetime.timezone(datetime.timedelta(hours=1)))
    elem = gpx._create_datetime_element(ns="timo", tag="birth", value=dt)
    assert elem.tag == "{timo}birth"
    assert elem.text == "1987-12-19T14:30:20Z"


def test_create_datetime_element_without_tzinfo():
    dt = datetime.datetime(
        year=1987, month=12, day=19, hour=15, minute=30, second=20)
    elem = gpx._create_datetime_element(ns="timo", tag="birth", value=dt)
    assert elem.tag == "{timo}birth"
    assert elem.text == "1987-12-19T15:30:20Z"


def test_create_decimal_element():
    elem = gpx._create_decimal_element(ns="timo", tag="number", value=-42.5)
    assert elem.tag == '{timo}number'
    assert float(elem.text) == -42.5


def test_create_garmin_track_point_extension_element():
    track_point = create_autospec(TrackPoint)
    track_point.heart_rate = 150
    ns = 'http://www.garmin.com/xmlschemas/TrackPointExtension/v2'
    elem = gpx._create_garmin_track_point_extension_element(track_point)
    assert elem.tag == ("{%s}TrackPointExtension" % ns)
    print(etree.tostring(elem))
    assert int(elem.find('{%s}hr' % ns).text) == 150


@patch("sq100.gpx._create_metadata_element", autospec=True)
@patch("sq100.gpx._create_track_element", autospec=True)
@patch('sq100.gpx.calc_tracks_bounds', autospec=True)
def test_create_gpx_element(mock_calc_tracks_bounds,
                            mock_create_track_element,
                            mock_create_metadata_element):
    tracks = ["track 1", "track 2"]
    mock_calc_tracks_bounds.return_value = "the bounds"
    mock_create_metadata_element.return_value = etree.Element("metadata")
    mock_create_track_element.side_effect = (
        lambda track, number: etree.Element(
            'trk', attrib={'number': str(number), 'data': track}))
    elem = gpx._create_gpx_element(tracks)
    assert elem.tag == 'gpx'
    assert len(elem.findall('trk')) == 2
    assert elem.findall('trk')[0].get('data') == 'track 1'
    assert elem.findall('trk')[0].get('number') == '0'
    assert elem.findall('trk')[1].get('data') == 'track 2'
    assert elem.findall('trk')[1].get('number') == '1'
    assert len(elem.findall('metadata')) == 1


@patch('sq100.gpx._create_bounds_element', autospec=True)
def test_create_metadata_element(mock_create_bounds_element):
    bounds = "the bounds"
    date = datetime.datetime(1987, 12, 19, 15, 30, 12)
    name = "my name"
    description = "my metadata description"
    ns = "timo"
    mock_create_bounds_element.side_effect = (
        lambda ns, tag, value: etree.Element("{%s}%s" % (ns, tag),
                                             attrib={"bounds": value}))
    elem = gpx._create_metadata_element(bounds=bounds, date=date, name=name,
                                        description=description, ns=ns)
    assert elem.find('{%s}name' % ns).text == name
    assert elem.find('{%s}desc' % ns).text == description
    assert elem.find('{%s}time' % ns).text == '1987-12-19T15:30:12Z'
    assert elem.find('{%s}bounds' % ns).get('bounds') == bounds


def test_create_string_element():
    elem = gpx._create_string_element(ns="timo", tag="name", value="nachstedt")
    assert elem.tag == "{timo}name"
    assert elem.text == "nachstedt"


@patch('sq100.gpx._create_track_segment_element', autospec=True)
def test_create_track_element(mock_create_segment_element):
    ns = '{%s}' % gpx.gpx_ns
    mock_create_segment_element.return_value = etree.Element(ns + "trkseg")
    track = Track(name="timo", id=5, description="my track")
    src = "My heart rate computer"
    number = 10
    elem = gpx._create_track_element(track=track, number=number, src=src)
    assert elem.find(ns + 'name').text == "timo"
    assert elem.find(ns + 'cmt').text == "id=5"
    assert elem.find(ns + "desc").text == "my track"
    assert int(elem.find(ns + "number").text) == 10
    assert elem.find(ns + 'src').text == "My heart rate computer"
    assert elem.find(ns + 'trkseg') is not None


@patch('sq100.gpx._create_track_point_extensions_element', autospec=True)
def test_create_track_point_element(mock_create_extensions_elem):
    ns = '{%s}' % gpx.gpx_ns
    mock_create_extensions_elem.return_value = etree.Element(ns + 'extensions')
    tp = TrackPoint(latitude=23.4, longitude=-32.1, altitude=678.51,
                    date=datetime.datetime(1987, 12, 19, 15, 30, 20))
    elem = gpx._create_track_point_element(tp)
    assert float(elem.get('lat')) == tp.latitude
    assert float(elem.get('lon')) == tp.longitude
    assert float(elem.find(ns + 'ele').text) == tp.altitude
    assert elem.find(ns + 'time').text == '1987-12-19T15:30:20Z'
    assert elem.find(ns + 'extensions') is not None


@patch('sq100.gpx._create_garmin_track_point_extension_element', autospec=True)
def test_create_track_point_extensions_element(mock_create_garmin_element):
    mock_create_garmin_element.return_value = etree.Element("garmin")
    track_point = TrackPoint()
    elem = gpx._create_track_point_extensions_element(track_point)
    assert elem.tag == "{%s}%s" % (gpx.gpx_ns, 'extensions')
    assert elem.find('garmin') is not None
    mock_create_garmin_element.assert_called_once_with(track_point)


@patch('sq100.gpx._create_track_point_element', autospec=True)
def test_create_track_segment_element(mock_create_track_point_element):
    track = Track(track_points=["tp1", "tp2", "tp3"])
    mock_create_track_point_element.side_effect = (
        lambda tp: etree.Element('trkpt', attrib={"foo": tp}))
    elem = gpx._create_track_segment_element(track)
    assert elem.tag == "{%s}%s" % (gpx.gpx_ns, 'trkseg')
    assert elem.findall('trkpt')[0].get('foo') == "tp1"
    assert elem.findall('trkpt')[1].get('foo') == "tp2"
    assert elem.findall('trkpt')[2].get('foo') == "tp3"


def test_indent():
    elem = etree.Element('main')
    etree.SubElement(elem, "suba")
    gpx._indent(elem)
    expected = "<main>\n  <suba />\n</main>\n"
    actual = etree.tostring(elem, encoding='unicode')
    assert actual == expected


@patch('sq100.gpx.etree.ElementTree', autospec=True)
@patch('sq100.gpx._create_gpx_element', autospec=True)
def test_tracks_to_gpx(mock_create_gpx_element, mock_element_tree):
    tracks = [Track(), Track()]
    filename = 'tmp.gpx'
    mock_create_gpx_element.return_value = etree.Element("gpx")
    mock_doc = mock_element_tree.return_value
    gpx.tracks_to_gpx(tracks, filename)
    mock_doc.write.assert_called_once()
    assert mock_doc.write.call_args[0][0] == "tmp.gpx"
