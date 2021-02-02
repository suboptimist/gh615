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
from typing import List

import xml.etree.ElementTree as etree

from sq100.data_types import CoordinateBounds, Track, TrackPoint
from sq100.utilities import calc_tracks_bounds

"namespacces"
gpx_ns = "http://www.topografix.com/GPX/1/1"
gpx_ns_def = "http://www.topografix.com/GPX/1/1/gpx.xsd"
xsi_ns = "http://www.w3.org/2001/XMLSchema-instance"
tpex_ns = 'http://www.garmin.com/xmlschemas/TrackPointExtension/v2'
tpex_ns_def = "https://www8.garmin.com/xmlschemas/TrackPointExtensionv2.xsd"


def _create_bounds_element(
    value: CoordinateBounds, ns: str = gpx_ns, tag: str = 'bounds'
) -> etree.Element:
    elem = etree.Element(str(etree.QName(ns, tag)))
    elem.set("minlat", str(value.min.latitude))
    elem.set("minlon", str(value.min.longitude))
    elem.set("maxlat", str(value.max.latitude))
    elem.set("maxlon", str(value.max.longitude))
    return elem


def _create_datetime_element(
    ns: str,
    tag: str,
    value: datetime.datetime
) -> etree.Element:
    utcoffset = value.utcoffset()
    if utcoffset is not None:
        value = (value - utcoffset).replace(tzinfo=None)
    return _create_string_element(ns, tag, "%sZ" % value.isoformat())


def _create_decimal_element(ns: str, tag: str, value: float) -> etree.Element:
    return _create_string_element(ns, tag, str(value))


def _create_garmin_track_point_extension_element(
        track_point: TrackPoint, ns: str = tpex_ns) -> etree.Element:
    trkptex = etree.Element(str(etree.QName(ns, "TrackPointExtension")))
    trkptex.append(
        _create_decimal_element(tpex_ns, "hr", track_point.heart_rate))
    return trkptex


def _create_gpx_element(tracks: List[Track]) -> etree.Element:
    gpx = etree.Element('gpx')
    gpx.set('version', '1.1')
    gpx.set("creator", 'https://github.com/tnachstedt/sq100')
    gpx.set(str(etree.QName(xsi_ns, "schemaLocation")),
            "%s %s %s %s" % (gpx_ns, gpx_ns_def, tpex_ns, tpex_ns_def))
    bounds = calc_tracks_bounds(tracks)
    if bounds is not None:
        gpx.append(_create_metadata_element(bounds=bounds))
    for i, track in enumerate(tracks):
        gpx.append(_create_track_element(track=track, number=i))
    return gpx


def _create_metadata_element(
        bounds: CoordinateBounds,
        name: str = "SQ100 Tracks",
        description: str = "Tracks export from the SQ100 application",
        date: datetime.datetime = datetime.datetime.now(),
        ns: str = gpx_ns,
        tag: str = 'metadata'
) -> etree.Element:
    metadata = etree.Element(str(etree.QName(ns, tag)))
    metadata.append(
        _create_string_element(ns=ns, tag="name", value=name))
    metadata.append(
        _create_string_element(ns=ns, tag="desc", value=description))
    metadata.append(_create_datetime_element(ns=ns, tag="time", value=date))
    metadata.append(_create_bounds_element(ns=ns, tag="bounds", value=bounds))
    return metadata


def _create_string_element(ns: str, tag: str, value: str) -> etree.Element:
    elem = etree.Element(str(etree.QName(ns, tag)))
    elem.text = value
    return elem


def _create_track_element(
        track: Track,
        number: int,
        src: str = "Arival SQ100 computer",
        ns: str = gpx_ns,
        tag: str = "trk"
) -> etree.Element:
    elem = etree.Element(str(etree.QName(ns, tag)))
    elem.append(_create_string_element(
        ns=gpx_ns, tag="cmt", value="id=%s" % track.info.id))
    elem.append(_create_string_element(ns=gpx_ns, tag="src", value=src))
    elem.append(_create_decimal_element(ns=gpx_ns, tag="number", value=number))
    elem.append(_create_track_segment_element(
        track_points=track.track_points, start_date=track.info.date))
    return elem


def _create_track_point_element(
        track_point: TrackPoint,
        date: datetime.datetime,
        ns: str = gpx_ns,
        tag: str = 'trkpt'
) -> etree.Element:
    trkpt = etree.Element(str(etree.QName(ns, tag)))
    trkpt.set("lat", str(track_point.latitude))
    trkpt.set("lon", str(track_point.longitude))
    trkpt.append(_create_decimal_element(gpx_ns, "ele", track_point.altitude))
    trkpt.append(_create_datetime_element(gpx_ns, "time", date))
    trkpt.append(_create_track_point_extensions_element(track_point))
    return trkpt


def _create_track_point_extensions_element(
        track_point: TrackPoint,
        ns: str = gpx_ns,
        tag: str = "extensions"
) -> etree.Element:
    extensions = etree.Element(str(etree.QName(ns, tag)))
    extensions.append(
        _create_garmin_track_point_extension_element(track_point))
    return extensions


def _create_track_segment_element(
        track_points: List[TrackPoint],
        start_date: datetime.datetime,
        ns: str = gpx_ns,
        tag: str = "trkseg"
) -> etree.Element:
    segment = etree.Element(str(etree.QName(ns, tag)))
    date = start_date
    for track_point in track_points:
        segment.append(_create_track_point_element(track_point, date=date))
        date += track_point.interval
    return segment


def _indent(elem: etree.Element, level: int = 0) -> None:
    '''
    copy and paste from http://effbot.org/zone/element-lib.htm#prettyprint
    '''
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            _indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def tracks_to_gpx(tracks: List[Track], filename: str) -> None:
    gpx = _create_gpx_element(tracks)
    _indent(gpx)
    doc = etree.ElementTree(gpx)
    etree.register_namespace('', gpx_ns)
    etree.register_namespace('gpxtpx', tpex_ns)
    doc.write(filename,
              encoding="UTF-8",
              xml_declaration=True,
              method='xml')
