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
from pathlib import Path
from typing import List, Optional
import xml.etree.ElementTree as etree

from sq100 import gpx


def make_gpx_root(
    metadata: Optional[gpx.Metadata] = None,
    tracks: Optional[List[gpx.Track]] = None,
) -> gpx.GpxRoot:
    return gpx.GpxRoot(
        metadata=metadata or make_metadata(),
        tracks=tracks or [])


def make_metadata(
    name: str = "the name",
    description: str = "the description",
    time: datetime.datetime = datetime.datetime(2000, 1, 1),
    bounds: Optional[gpx.Bounds] = None,
) -> gpx.Metadata:
    return gpx.Metadata(
        name=name,
        description=description,
        time=time,
        bounds=bounds,
    )


def make_track(
    comment: str = "the comment",
    src: str = "the src",
    number: int = 0,
    track_points: Optional[List[gpx.TrackPoint]] = None
) -> gpx.Track:
    return gpx.Track(
        comment=comment,
        src=src,
        number=number,
        track_points=track_points or [],
    )


def make_track_point(
    latitude: float = 0,
    longitude: float = 0,
    elevation: float = 0,
    time: datetime.datetime = datetime.datetime(2000, 1, 1),
    heart_rate: float = 0,
) -> gpx.TrackPoint:
    return gpx.TrackPoint(
        latitude=latitude,
        longitude=longitude,
        elevation=elevation,
        time=time,
        heart_rate=heart_rate,
    )


def test_bounds__to_etree() -> None:
    bounds = gpx.Bounds(minlat=10.8, minlon=-8.1, maxlat=25.0, maxlon=-2.9)
    elem = bounds.to_etree()
    assert float(elem.get("minlat", "0")) == 10.8
    assert float(elem.get("minlon", "0")) == -8.1
    assert float(elem.get("maxlat", "0")) == 25.0
    assert float(elem.get("maxlon", "0")) == -2.9


def test_create_datetime_element_with_tzinfo() -> None:
    dt = datetime.datetime(
        year=1987, month=12, day=19, hour=15, minute=30, second=20,
        tzinfo=datetime.timezone(datetime.timedelta(hours=1)))
    elem = gpx.make_datetime_element(ns="timo", tag="birth", value=dt)
    assert elem.tag == "{timo}birth"
    assert elem.text == "1987-12-19T14:30:20Z"


def test_create_datetime_element_without_tzinfo() -> None:
    dt = datetime.datetime(
        year=1987, month=12, day=19, hour=15, minute=30, second=20)
    elem = gpx.make_datetime_element(ns="timo", tag="birth", value=dt)
    assert elem.tag == "{timo}birth"
    assert elem.text == "1987-12-19T15:30:20Z"


def test_create_decimal_element() -> None:
    elem = gpx.make_decimal_element(ns="timo", tag="number", value=-42.5)
    assert elem.tag == '{timo}number'
    assert elem.text is not None
    assert float(elem.text) == -42.5


def test_make_garmin_track_point_extension_element() -> None:
    ns = 'http://www.garmin.com/xmlschemas/TrackPointExtension/v2'
    elem = gpx.make_garmin_track_point_extension_element(heart_rate=150)
    heart_rate_element = elem.find('{%s}hr' % ns)
    assert elem.tag == ("{%s}TrackPointExtension" % ns)
    assert heart_rate_element is not None
    assert heart_rate_element.text is not None
    assert int(heart_rate_element.text) == 150


def test_gpx_root__to_etree() -> None:
    gpx_root = gpx.GpxRoot(
        metadata=gpx.Metadata(
            name="my_test",
            description="my_description",
            time=datetime.datetime(1987, 12, 19, 1, 2, 3),
            bounds=None),
        tracks=[
            make_track(
                number=11,
                track_points=[make_track_point(latitude=-1, longitude=2)]),
            make_track(
                number=22,
                track_points=[make_track_point(latitude=3, longitude=-4)]),
        ]
    )
    elem = gpx_root.to_etree()

    ns = '{%s}' % gpx.gpx_ns
    assert elem.tag == 'gpx'
    gpx_tracks = elem.findall(ns + 'trk')
    assert len(gpx_tracks) == 2
    gpx_number_0 = gpx_tracks[0].find(ns + 'number')
    gpx_number_1 = gpx_tracks[1].find(ns + 'number')
    assert gpx_number_0 is not None
    assert gpx_number_1 is not None
    assert gpx_number_0.text == '11'
    assert gpx_number_1.text == '22'
    assert len(elem.findall(ns + 'metadata')) == 1


def test_metadata__to_etree() -> None:
    metadata = gpx.Metadata(
        name="my name",
        description="my metadata description",
        time=datetime.datetime(1987, 12, 19, 15, 30, 12),
        bounds=gpx.Bounds(minlat=1., minlon=2., maxlat=3., maxlon=4.)
    )
    elem = metadata.to_etree()
    ns = '{' + gpx.gpx_ns + '}'
    name_element = elem.find(f'{ns}name')
    desc_element = elem.find(f'{ns}desc')
    time_element = elem.find(f'{ns}time')
    bounds_element = elem.find(f'{ns}bounds')
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
    elem = gpx.make_string_element(ns="timo", tag="name", value="nachstedt")
    assert elem.tag == "{timo}name"
    assert elem.text == "nachstedt"


def test_track__to_etree() -> None:
    track = gpx.Track(
        comment="the comment",
        src="the src",
        number=3,
        track_points=[make_track_point(latitude=4)]
    )
    elem = track.to_etree()
    ns = '{%s}' % gpx.gpx_ns
    cmt_element = elem.find(ns + 'cmt')
    src_element = elem.find(ns + 'src')
    assert cmt_element is not None
    assert src_element is not None
    assert cmt_element.text == "the comment"
    assert src_element.text == "the src"
    assert elem.find(ns + 'trkseg') is not None


def test_track_point__to_etree() -> None:
    track_point = gpx.TrackPoint(
        latitude=23.4,
        longitude=-32.1,
        elevation=678.51,
        time=datetime.datetime(1987, 12, 19, 15, 30, 20),
        heart_rate=42
    )

    ns = '{%s}' % gpx.gpx_ns
    elem = track_point.to_etree()
    assert float(elem.get('lat', -1)) == 23.4
    assert float(elem.get('lon', -1)) == -32.1
    elevation_element = elem.find(ns + 'ele')
    assert elevation_element is not None
    assert elevation_element.text == "678.51"
    time_element = elem.find(ns + 'time')
    assert time_element is not None
    assert time_element.text == '1987-12-19T15:30:20Z'
    assert elem.find(ns + 'extensions') is not None


def test_make_track_point_extensions_element() -> None:
    elem = gpx.make_track_point_extensions_element(heart_rate=42)
    assert elem.tag == "{%s}%s" % (gpx.gpx_ns, 'extensions')
    garmin = '{%s}%s' % (gpx.tpex_ns, 'TrackPointExtension')
    assert elem.find(garmin) is not None


def test_make_track_segment_element() -> None:
    track_points = [
        make_track_point(
            latitude=1, time=datetime.datetime(2000, 1, 1, 12, 1, 1)),
        make_track_point(
            latitude=2, time=datetime.datetime(2000, 1, 1, 12, 2, 2))]
    elem = gpx.make_track_segment_element(track_points=track_points)
    assert elem.tag == "{%s}%s" % (gpx.gpx_ns, 'trkseg')
    trkpt = '{' + gpx.gpx_ns + '}trkpt'
    time = '{' + gpx.gpx_ns + '}time'
    assert elem.findall(trkpt)[0].get('lat') == "1"
    time_0 = elem.findall(trkpt)[0].find(time)
    assert time_0 is not None
    assert time_0.text == "2000-01-01T12:01:01Z"
    assert elem.findall(trkpt)[1].get('lat') == "2"
    time_1 = elem.findall(trkpt)[1].find(time)
    assert time_1 is not None
    assert time_1.text == "2000-01-01T12:02:02Z"


def test_indent() -> None:
    elem = etree.Element('main')
    etree.SubElement(elem, "suba")
    gpx._indent(elem)
    expected = "<main>\n  <suba />\n</main>\n"
    actual = etree.tostring(elem, encoding='unicode')
    assert actual == expected


def test_stoe_tracks_to_file(tmp_path: Path) -> None:
    tracks = [make_track(), make_track()]
    filename = str(tmp_path / 'tmp.gpx')
    gpx.store_tracks_to_file(tracks, filename=filename)


def test_calc_track_bounds__returns_correct_bounds() -> None:
    bounds = gpx.calc_tracks_bounds(
        tracks=[
            make_track(track_points=[
                make_track_point(latitude=1.0, longitude=2.0)]),
            make_track(track_points=[
                make_track_point(latitude=3.0, longitude=-4.0)])])
    assert bounds is not None
    assert bounds.minlat == 1.0
    assert bounds.minlon == -4.0
    assert bounds.maxlat == 3.0
    assert bounds.maxlon == 2.0


def test_calc_track_bounds__returns_none_for_no_tracks() -> None:
    assert gpx.calc_tracks_bounds(tracks=[]) is None


def test_calc_track_bounds__returns_none_for_empty_tracks() -> None:
    assert gpx.calc_tracks_bounds(tracks=[make_track(), make_track()]) is None
