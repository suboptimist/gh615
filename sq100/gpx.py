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

from dataclasses import dataclass
import datetime
from typing import List, Optional

import xml.etree.ElementTree as etree


"namespacces"
gpx_ns = "http://www.topografix.com/GPX/1/1"
gpx_ns_def = "http://www.topografix.com/GPX/1/1/gpx.xsd"
xsi_ns = "http://www.w3.org/2001/XMLSchema-instance"
tpex_ns = "http://www.garmin.com/xmlschemas/TrackPointExtension/v2"
tpex_ns_def = "https://www8.garmin.com/xmlschemas/TrackPointExtensionv2.xsd"


@dataclass
class Bounds:
    minlat: float
    minlon: float
    maxlat: float
    maxlon: float

    def to_etree(self, ns: str = gpx_ns, tag: str = "bounds") -> etree.Element:
        elem = etree.Element(str(etree.QName(ns, tag)))
        elem.set("minlat", str(self.minlat))
        elem.set("minlon", str(self.minlon))
        elem.set("maxlat", str(self.maxlat))
        elem.set("maxlon", str(self.maxlon))
        return elem


@dataclass
class Metadata:
    name: str
    description: str
    time: datetime.datetime
    bounds: Optional[Bounds]

    def to_etree(self) -> etree.Element:
        elem = etree.Element(str(etree.QName(gpx_ns, "metadata")))
        elem.append(make_string_element(ns=gpx_ns, tag="name", value=self.name))
        elem.append(make_string_element(ns=gpx_ns, tag="desc", value=self.description))
        elem.append(make_datetime_element(ns=gpx_ns, tag="time", value=self.time))
        if self.bounds is not None:
            elem.append(self.bounds.to_etree())
        return elem


@dataclass
class TrackPoint:
    latitude: float
    longitude: float
    elevation: float
    time: datetime.datetime
    heart_rate: float

    def to_etree(self) -> etree.Element:
        elem = etree.Element(str(etree.QName(gpx_ns, "trkpt")))
        elem.set("lat", str(self.latitude))
        elem.set("lon", str(self.longitude))
        elem.append(make_decimal_element(gpx_ns, "ele", self.elevation))
        elem.append(make_datetime_element(gpx_ns, "time", self.time))
        elem.append(make_track_point_extensions_element(heart_rate=self.heart_rate))
        return elem


@dataclass
class Track:
    comment: str
    src: str
    number: int
    track_points: List[TrackPoint]

    def to_etree(self) -> etree.Element:
        elem = etree.Element(str(etree.QName(gpx_ns, "trk")))
        elem.append(make_string_element(ns=gpx_ns, tag="cmt", value=self.comment))
        elem.append(make_string_element(ns=gpx_ns, tag="src", value=self.src))
        elem.append(make_decimal_element(ns=gpx_ns, tag="number", value=self.number))
        elem.append(make_track_segment_element(self.track_points))
        return elem


@dataclass
class GpxRoot:
    metadata: Metadata
    tracks: List[Track]

    def to_etree(self) -> etree.Element:
        elem = etree.Element("gpx")
        elem.set("version", "1.1")
        elem.set("creator", "https://github.com/tnachstedt/sq100")
        elem.set(
            str(etree.QName(xsi_ns, "schemaLocation")),
            f"{gpx_ns} {gpx_ns_def} {tpex_ns} {tpex_ns_def}",
        )
        elem.append(self.metadata.to_etree())
        for track in self.tracks:
            elem.append(track.to_etree())
        return elem


def store_tracks_to_file(tracks: List[Track], filename: str) -> None:
    gpx = GpxRoot(
        metadata=Metadata(
            name="SQ100 Tracks",
            description="Tracks export from the SQ100 application",
            time=datetime.datetime.now(),
            bounds=calc_tracks_bounds(tracks),
        ),
        tracks=tracks,
    )
    elem = gpx.to_etree()
    _indent(elem)
    doc = etree.ElementTree(elem)
    etree.register_namespace("", gpx_ns)
    etree.register_namespace("gpxtpx", tpex_ns)
    doc.write(filename, encoding="UTF-8", xml_declaration=True, method="xml")


def calc_tracks_bounds(tracks: List[Track]) -> Optional[Bounds]:
    track_points: List[TrackPoint] = sum((track.track_points for track in tracks), [])
    if len(track_points) == 0:
        return None
    return Bounds(
        minlat=min([p.latitude for p in track_points]),
        maxlat=max([p.latitude for p in track_points]),
        minlon=min([p.longitude for p in track_points]),
        maxlon=max([p.longitude for p in track_points]),
    )


def _indent(elem: etree.Element, level: int = 0) -> None:
    """
    copy and paste from http://effbot.org/zone/element-lib.htm#prettyprint
    """
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


def make_datetime_element(ns: str, tag: str, value: datetime.datetime) -> etree.Element:
    utcoffset = value.utcoffset()
    if utcoffset is not None:
        value = (value - utcoffset).replace(tzinfo=None)
    return make_string_element(ns, tag, "%sZ" % value.isoformat())


def make_decimal_element(ns: str, tag: str, value: float) -> etree.Element:
    return make_string_element(ns, tag, str(value))


def make_track_point_extensions_element(heart_rate: float) -> etree.Element:
    extensions = etree.Element(str(etree.QName(gpx_ns, "extensions")))
    extensions.append(make_garmin_track_point_extension_element(heart_rate=heart_rate))
    return extensions


def make_garmin_track_point_extension_element(heart_rate: float) -> etree.Element:
    trkptex = etree.Element(str(etree.QName(tpex_ns, "TrackPointExtension")))
    trkptex.append(make_decimal_element(tpex_ns, "hr", heart_rate))
    return trkptex


def make_track_segment_element(track_points: List[TrackPoint]) -> etree.Element:
    segment = etree.Element(str(etree.QName(gpx_ns, "trkseg")))
    for track_point in track_points:
        segment.append(track_point.to_etree())
    return segment


def make_string_element(ns: str, tag: str, value: str) -> etree.Element:
    elem = etree.Element(str(etree.QName(ns, tag)))
    elem.text = value
    return elem
