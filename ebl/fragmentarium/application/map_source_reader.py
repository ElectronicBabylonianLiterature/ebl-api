from __future__ import annotations

import codecs
import math
from pathlib import Path
import struct

from ebl.fragmentarium.application.map_geometry import (
    MultiPolygon,
    polygonize_rings,
    strict_zip,
)


def load_dbf_encoding(path: Path) -> str:
    try:
        encoding = path.read_text(encoding="utf-8-sig").strip()
    except (OSError, UnicodeError) as error:
        raise ValueError(f"Cannot read required DBF encoding file {path}.") from error
    if not encoding:
        raise ValueError(f"DBF encoding file {path} is blank.")
    try:
        codecs.lookup(encoding)
    except LookupError as error:
        raise ValueError(f"Unknown DBF encoding {encoding!r} in {path}.") from error
    return encoding


def load_prj_wkt(path: Path) -> str:
    try:
        wkt = path.read_text(encoding="utf-8-sig").strip()
    except (OSError, UnicodeError) as error:
        raise ValueError(f"Cannot read required shapefile CRS file {path}.") from error
    if not wkt:
        raise ValueError(f"Shapefile CRS file {path} is blank.")
    return wkt


def load_dbf_rows(path: Path, encoding: str) -> tuple[dict[str, str], ...]:
    with path.open("rb") as file_:
        header = file_.read(32)
        if len(header) != 32:
            raise ValueError(f"Truncated DBF header in {path}.")
        if header[0] != 3:
            raise ValueError(f"Unsupported DBF version in {path}.")
        record_count = struct.unpack("<I", header[4:8])[0]
        header_length = struct.unpack("<H", header[8:10])[0]
        record_length = struct.unpack("<H", header[10:12])[0]
        if header_length < 33 or (header_length - 33) % 32:
            raise ValueError(f"Invalid DBF header length in {path}.")
        field_count = (header_length - 33) // 32
        fields = []
        for _ in range(field_count):
            descriptor = file_.read(32)
            if len(descriptor) != 32:
                raise ValueError(f"Truncated DBF field descriptor in {path}.")
            name = descriptor[:11].split(b"\x00", 1)[0].decode("ascii")
            length = descriptor[16]
            if (
                not name
                or not length
                or any(existing == name for existing, _ in fields)
            ):
                raise ValueError(f"Invalid DBF field descriptor in {path}.")
            fields.append((name, length))
        if file_.read(1) != b"\x0d":
            raise ValueError(f"Missing DBF field descriptor terminator in {path}.")
        if record_length != 1 + sum(length for _, length in fields):
            raise ValueError(f"Invalid DBF record length in {path}.")
        rows = []
        for _ in range(record_count):
            record = file_.read(record_length)
            if len(record) != record_length:
                raise ValueError(f"Truncated DBF record in {path}.")
            if record[:1] == b"*":
                raise ValueError(f"Deleted DBF records are unsupported in {path}.")
            if record[:1] != b" ":
                raise ValueError(f"Invalid DBF record marker in {path}.")
            position = 1
            row = {}
            for name, length in fields:
                row[name] = (
                    record[position : position + length].decode(encoding).strip()
                )
                position += length
            rows.append(row)
        trailing = file_.read()
        if trailing not in (b"", b"\x1a"):
            raise ValueError(f"Unexpected trailing bytes in {path}.")
    return tuple(rows)


def load_shp_polygon_geometries(path: Path) -> tuple[MultiPolygon, ...]:
    geometries = []
    with path.open("rb") as file_:
        header = file_.read(100)
        if len(header) != 100:
            raise ValueError(f"Truncated shapefile header in {path}.")
        if struct.unpack(">i", header[:4])[0] != 9994:
            raise ValueError(f"Invalid shapefile file code in {path}.")
        declared_length = struct.unpack(">i", header[24:28])[0] * 2
        if declared_length != path.stat().st_size:
            raise ValueError(f"Shapefile declared length does not match {path}.")
        if struct.unpack("<i", header[28:32])[0] != 1000:
            raise ValueError(f"Unsupported shapefile version in {path}.")
        if struct.unpack("<i", header[32:36])[0] != 5:
            raise ValueError(f"Only polygon shapefiles are supported: {path}.")
        expected_record_number = 1
        while True:
            header = file_.read(8)
            if not header:
                break
            if len(header) != 8:
                raise ValueError(f"Truncated shapefile record header in {path}.")
            record_number, content_length = struct.unpack(">2i", header)
            if record_number != expected_record_number or content_length < 22:
                raise ValueError(f"Invalid shapefile record header in {path}.")
            content = file_.read(content_length * 2)
            if len(content) != content_length * 2:
                raise ValueError(f"Truncated shapefile record in {path}.")
            if struct.unpack("<i", content[:4])[0] != 5:
                raise ValueError("Only polygon shapefile records are supported.")
            number_of_parts, number_of_points = struct.unpack("<2i", content[36:44])
            expected_length = 44 + 4 * number_of_parts + 16 * number_of_points
            if (
                number_of_parts < 1
                or number_of_points < 4
                or len(content) != expected_length
            ):
                raise ValueError(f"Invalid polygon record dimensions in {path}.")
            parts = struct.unpack(
                "<" + "i" * number_of_parts, content[44 : 44 + 4 * number_of_parts]
            )
            if (
                parts[0] != 0
                or any(
                    left >= right for left, right in strict_zip(parts[:-1], parts[1:])
                )
                or parts[-1] >= number_of_points
            ):
                raise ValueError(f"Invalid polygon part indexes in {path}.")
            points_offset = 44 + 4 * number_of_parts
            points = tuple(
                struct.unpack(
                    "<2d",
                    content[
                        points_offset + 16 * index : points_offset + 16 * (index + 1)
                    ],
                )
                for index in range(number_of_points)
            )
            if any(
                not math.isfinite(coordinate)
                for point in points
                for coordinate in point
            ):
                raise ValueError(f"Non-finite polygon coordinate in {path}.")
            part_bounds = parts + (number_of_points,)
            rings = tuple(
                points[start:end]
                for start, end in strict_zip(part_bounds[:-1], part_bounds[1:])
            )
            if any(len(ring) < 4 or ring[0] != ring[-1] for ring in rings):
                raise ValueError(f"Invalid unclosed polygon ring in {path}.")
            geometries.append(polygonize_rings(rings))
            expected_record_number += 1
    return tuple(geometries)
