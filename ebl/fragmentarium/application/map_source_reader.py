from __future__ import annotations

from pathlib import Path
import struct

from ebl.fragmentarium.application.map_geometry import Rings, strict_zip


def load_dbf_encoding(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip() if path.exists() else "latin1"


def load_prj_wkt(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def load_dbf_rows(path: Path, encoding: str) -> tuple[dict[str, str], ...]:
    with path.open("rb") as file_:
        header = file_.read(32)
        record_count = struct.unpack("<I", header[4:8])[0]
        record_length = struct.unpack("<H", header[10:12])[0]
        fields = []
        while True:
            marker = file_.read(1)
            if marker == b"\x0d":
                break
            descriptor = marker + file_.read(31)
            name = descriptor[:11].split(b"\x00", 1)[0].decode("latin1")
            fields.append((name, descriptor[16]))
        rows = []
        for _ in range(record_count):
            record = file_.read(record_length)
            position = 1
            row = {}
            for name, length in fields:
                row[name] = (
                    record[position : position + length].decode(encoding).strip()
                )
                position += length
            rows.append(row)
    return tuple(rows)


def load_shp_polygon_rings(path: Path) -> tuple[Rings, ...]:
    rings_by_feature = []
    with path.open("rb") as file_:
        file_.read(100)
        while True:
            header = file_.read(8)
            if not header:
                break
            _, content_length = struct.unpack(">2i", header)
            content = file_.read(content_length * 2)
            if struct.unpack("<i", content[:4])[0] != 5:
                raise ValueError("Only polygon shapefile records are supported.")
            number_of_parts, number_of_points = struct.unpack("<2i", content[36:44])
            parts = struct.unpack(
                "<" + "i" * number_of_parts, content[44 : 44 + 4 * number_of_parts]
            )
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
            part_bounds = parts + (number_of_points,)
            rings_by_feature.append(
                tuple(
                    points[start:end]
                    for start, end in strict_zip(part_bounds[:-1], part_bounds[1:])
                )
            )
    return tuple(rings_by_feature)
