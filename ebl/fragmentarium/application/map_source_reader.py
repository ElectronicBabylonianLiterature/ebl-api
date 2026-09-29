from __future__ import annotations

import math
from pathlib import Path
import struct
from typing import BinaryIO, Iterator

from ebl.fragmentarium.application.map_geometry import (
    MultiPolygon,
    Point,
    Rings,
    polygonize_rings,
    strict_zip,
)

SHP_HEADER_LENGTH = 100
POLYGON_SHAPE_TYPE = 5
POLYGON_POINTS_OFFSET = 44


def load_prj_wkt(path: Path) -> str:
    try:
        wkt = path.read_text(encoding="utf-8-sig").strip()
    except (OSError, UnicodeError) as error:
        raise ValueError(f"Cannot read required shapefile CRS file {path}.") from error
    if not wkt:
        raise ValueError(f"Shapefile CRS file {path} is blank.")
    return wkt


def load_shp_polygon_geometries(path: Path) -> tuple[MultiPolygon, ...]:
    with path.open("rb") as file_:
        _validate_shp_header(file_, path)
        return tuple(_read_polygon_records(file_, path))


def _validate_shp_header(file_: BinaryIO, path: Path) -> None:
    header = file_.read(SHP_HEADER_LENGTH)
    if len(header) != SHP_HEADER_LENGTH:
        raise ValueError(f"Truncated shapefile header in {path}.")
    if struct.unpack(">i", header[:4])[0] != 9994:
        raise ValueError(f"Invalid shapefile file code in {path}.")
    if struct.unpack(">i", header[24:28])[0] * 2 != path.stat().st_size:
        raise ValueError(f"Shapefile declared length does not match {path}.")
    if struct.unpack("<i", header[28:32])[0] != 1000:
        raise ValueError(f"Unsupported shapefile version in {path}.")
    if struct.unpack("<i", header[32:36])[0] != POLYGON_SHAPE_TYPE:
        raise ValueError(f"Only polygon shapefiles are supported: {path}.")


def _read_polygon_records(file_: BinaryIO, path: Path) -> Iterator[MultiPolygon]:
    expected_record_number = 1
    while content := _read_shp_record(file_, path, expected_record_number):
        yield _parse_polygon_record(content, path)
        expected_record_number += 1


def _read_shp_record(file_: BinaryIO, path: Path, expected_record_number: int) -> bytes:
    header = file_.read(8)
    if not header:
        return b""
    if len(header) != 8:
        raise ValueError(f"Truncated shapefile record header in {path}.")
    record_number, content_length = struct.unpack(">2i", header)
    if record_number != expected_record_number or content_length < 22:
        raise ValueError(f"Invalid shapefile record header in {path}.")
    content = file_.read(content_length * 2)
    if len(content) != content_length * 2:
        raise ValueError(f"Truncated shapefile record in {path}.")
    return content


def _parse_polygon_record(content: bytes, path: Path) -> MultiPolygon:
    if struct.unpack("<i", content[:4])[0] != POLYGON_SHAPE_TYPE:
        raise ValueError("Only polygon shapefile records are supported.")
    number_of_parts, number_of_points = struct.unpack("<2i", content[36:44])
    points_offset = POLYGON_POINTS_OFFSET + 4 * number_of_parts
    if (
        number_of_parts < 1
        or number_of_points < 4
        or len(content) != points_offset + 16 * number_of_points
    ):
        raise ValueError(f"Invalid polygon record dimensions in {path}.")
    parts = struct.unpack(
        "<" + "i" * number_of_parts, content[POLYGON_POINTS_OFFSET:points_offset]
    )
    _validate_part_indexes(parts, number_of_points, path)
    points = _unpack_points(content[points_offset:], path)
    return polygonize_rings(_split_rings(points, parts, path))


def _validate_part_indexes(
    parts: tuple[int, ...], number_of_points: int, path: Path
) -> None:
    if (
        parts[0] != 0
        or any(left >= right for left, right in strict_zip(parts[:-1], parts[1:]))
        or parts[-1] >= number_of_points
    ):
        raise ValueError(f"Invalid polygon part indexes in {path}.")


def _unpack_points(data: bytes, path: Path) -> tuple[Point, ...]:
    points = tuple(struct.iter_unpack("<2d", data))
    if any(not math.isfinite(coordinate) for point in points for coordinate in point):
        raise ValueError(f"Non-finite polygon coordinate in {path}.")
    return points


def _split_rings(
    points: tuple[Point, ...], parts: tuple[int, ...], path: Path
) -> Rings:
    part_bounds = parts + (len(points),)
    rings = tuple(
        points[start:end]
        for start, end in strict_zip(part_bounds[:-1], part_bounds[1:])
    )
    if any(len(ring) < 4 or ring[0] != ring[-1] for ring in rings):
        raise ValueError(f"Invalid unclosed polygon ring in {path}.")
    return rings
