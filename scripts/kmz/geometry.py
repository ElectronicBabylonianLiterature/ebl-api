from __future__ import annotations

import math
from typing import Iterable, Sequence
from xml.etree import ElementTree

from scripts.kmz.models import Coordinate


def parse_kml_coordinate(value: str) -> Coordinate:
    parts = value.strip().split(",")
    if len(parts) < 2:
        raise ValueError("KML coordinate must include longitude and latitude")

    try:
        longitude = float(parts[0])
        latitude = float(parts[1])
    except ValueError as error:
        raise ValueError("KML coordinate contains a non-numeric value") from error

    if not math.isfinite(latitude) or not -90 <= latitude <= 90:
        raise ValueError("Latitude must be finite and between -90 and 90")
    if not math.isfinite(longitude) or not -180 <= longitude <= 180:
        raise ValueError("Longitude must be finite and between -180 and 180")

    return {"latitude": latitude, "longitude": longitude}


def parse_kml_coordinate_sequence(value: str) -> tuple[Coordinate, ...]:
    coordinates = tuple(
        parse_kml_coordinate(token) for token in value.split() if token.strip()
    )
    if len(coordinates) >= 2 and coordinates[0] == coordinates[-1]:
        coordinates = coordinates[:-1]
    return coordinates


def _iter(
    element: ElementTree.Element, local_name: str
) -> Iterable[ElementTree.Element]:
    for child in element.iter():
        if _local_name(child.tag) == local_name:
            yield child


def _direct_child_text(element: ElementTree.Element, local_name: str) -> str | None:
    for child in list(element):
        if _local_name(child.tag) == local_name:
            return child.text
    return None


def _first_descendant_text(element: ElementTree.Element, local_name: str) -> str | None:
    for descendant in _iter(element, local_name):
        return descendant.text
    return None


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _parse_geometry_coordinates(
    node: ElementTree.Element,
) -> tuple[tuple[Coordinate, ...] | None, bool, bool]:
    """Return (coordinates, invalid, missing) parsed from a single geometry node."""
    coordinates_text = _first_descendant_text(node, "coordinates")
    if not coordinates_text or not coordinates_text.strip():
        return None, False, True
    try:
        return parse_kml_coordinate_sequence(coordinates_text), False, False
    except ValueError:
        return None, True, False


def _extract_point(
    placemark: ElementTree.Element,
) -> tuple[Coordinate | None, bool, bool]:
    missing = invalid = False
    for point in _iter(placemark, "Point"):
        coordinates, node_invalid, node_missing = _parse_geometry_coordinates(point)
        invalid = invalid or node_invalid
        missing = missing or node_missing
        if coordinates:
            return coordinates[0], invalid, missing
    return None, invalid, missing


def _extract_polygon(
    placemark: ElementTree.Element,
) -> tuple[tuple[Coordinate, ...], bool, bool]:
    missing = invalid = False
    for polygon in _iter(placemark, "Polygon"):
        coordinates, node_invalid, node_missing = _parse_geometry_coordinates(polygon)
        invalid = invalid or node_invalid
        missing = missing or node_missing
        if coordinates is not None and len(coordinates) >= 3:
            return coordinates, invalid, missing
        if coordinates is not None:
            invalid = True
    return (), invalid, missing


def _geometry_type(
    point: Coordinate | None, polygon: Sequence[Coordinate], has_line_string: bool
) -> str:
    types: list[str] = []
    if point:
        types.append("Point")
    if polygon:
        types.append("Polygon")
    if has_line_string:
        types.append("LineString")
    return "+".join(types) if types else "Unsupported"
