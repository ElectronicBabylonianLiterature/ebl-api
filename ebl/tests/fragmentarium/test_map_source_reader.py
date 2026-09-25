from pathlib import Path
import struct

import pytest

from ebl.fragmentarium.application.map_source_reader import (
    load_dbf_encoding,
    load_dbf_rows,
    load_prj_wkt,
    load_shp_polygon_geometries,
)


def _dbf_bytes(value: bytes = b"Room", trailing: bytes = b"\x1a") -> bytes:
    descriptor = bytearray(32)
    descriptor[:5] = b"Name\x00"
    descriptor[11] = ord("C")
    descriptor[16] = 8
    header = bytearray(32)
    header[0] = 3
    header[4:8] = struct.pack("<I", 1)
    header[8:10] = struct.pack("<H", 65)
    header[10:12] = struct.pack("<H", 9)
    record = b" " + value.ljust(8)
    return bytes(header) + bytes(descriptor) + b"\x0d" + record + trailing


def _shp_bytes(rings=None) -> bytes:
    if rings is None:
        rings = (((43.0, 35.0), (43.0, 35.1), (43.1, 35.1), (43.0, 35.0)),)
    points_by_ring = tuple(point for ring in rings for point in ring)
    points = b"".join(struct.pack("<2d", *point) for point in points_by_ring)
    xs = tuple(point[0] for point in points_by_ring)
    ys = tuple(point[1] for point in points_by_ring)
    bbox = (min(xs), min(ys), max(xs), max(ys))
    part_indexes = []
    next_index = 0
    for ring in rings:
        part_indexes.append(next_index)
        next_index += len(ring)
    content = (
        struct.pack("<i4d2i", 5, *bbox, len(rings), len(points_by_ring))
        + struct.pack("<" + "i" * len(rings), *part_indexes)
        + points
    )
    record = struct.pack(">2i", 1, len(content) // 2) + content
    file_length = (100 + len(record)) // 2
    header = struct.pack(">7i", 9994, 0, 0, 0, 0, 0, file_length)
    header += struct.pack("<2i8d", 1000, 5, *bbox, 0.0, 0.0, 0.0, 0.0)
    return header + record


def test_load_dbf_encoding_requires_a_nonblank_known_codec(tmp_path: Path):
    path = tmp_path / "source.cpg"
    with pytest.raises(ValueError, match="required"):
        load_dbf_encoding(path)

    path.write_text("not-a-codec")
    with pytest.raises(ValueError, match="Unknown"):
        load_dbf_encoding(path)

    path.write_text("  UTF-8  ")
    assert load_dbf_encoding(path) == "UTF-8"


def test_load_prj_wkt_requires_nonblank_content(tmp_path: Path):
    path = tmp_path / "source.prj"
    path.write_text(" \n")

    with pytest.raises(ValueError, match="blank"):
        load_prj_wkt(path)


def test_load_dbf_rows_reads_an_exact_structurally_valid_file(tmp_path: Path):
    path = tmp_path / "source.dbf"
    path.write_bytes(_dbf_bytes())

    assert load_dbf_rows(path, "ascii") == ({"Name": "Room"},)


@pytest.mark.parametrize(
    "contents, message",
    [
        (_dbf_bytes()[:20], "header"),
        (_dbf_bytes()[:-3], "record"),
        (_dbf_bytes(trailing=b"junk"), "trailing"),
    ],
)
def test_load_dbf_rows_rejects_malformed_structure(
    tmp_path: Path, contents: bytes, message: str
):
    path = tmp_path / "source.dbf"
    path.write_bytes(bytes(contents))

    with pytest.raises(ValueError, match=message):
        load_dbf_rows(path, "ascii")


def test_load_shp_polygon_geometries_reads_an_exact_polygon_file(tmp_path: Path):
    path = tmp_path / "source.shp"
    path.write_bytes(_shp_bytes())

    assert load_shp_polygon_geometries(path) == (
        ((((43.0, 35.0), (43.0, 35.1), (43.1, 35.1), (43.0, 35.0)),),),
    )


@pytest.mark.parametrize(
    "mutation, message", [("length", "length"), ("truncated", "length")]
)
def test_load_shp_polygon_geometries_rejects_inexact_file_structure(
    tmp_path: Path, mutation: str, message: str
):
    contents = bytearray(_shp_bytes())
    if mutation == "length":
        contents[24:28] = struct.pack(">i", 50)
    else:
        contents.pop()
    path = tmp_path / "source.shp"
    path.write_bytes(bytes(contents))

    with pytest.raises(ValueError, match=message):
        load_shp_polygon_geometries(path)


def test_load_shp_polygon_geometries_rejects_unclosed_ring(tmp_path: Path):
    path = tmp_path / "source.shp"
    path.write_bytes(
        _shp_bytes(
            (
                (
                    (43.0, 35.0),
                    (43.1, 35.0),
                    (43.1, 35.1),
                    (43.2, 35.2),
                ),
            )
        )
    )

    with pytest.raises(ValueError, match="unclosed"):
        load_shp_polygon_geometries(path)


def test_load_shp_polygon_geometries_preserves_holes_and_exteriors(tmp_path: Path):
    exterior = ((0.0, 0.0), (0.0, 10.0), (10.0, 10.0), (10.0, 0.0), (0.0, 0.0))
    hole = ((2.0, 2.0), (8.0, 2.0), (8.0, 8.0), (2.0, 8.0), (2.0, 2.0))
    second = ((20.0, 0.0), (20.0, 5.0), (25.0, 5.0), (25.0, 0.0), (20.0, 0.0))
    path = tmp_path / "source.shp"
    path.write_bytes(_shp_bytes((hole, second, exterior)))

    assert load_shp_polygon_geometries(path) == (((second,), (exterior, hole)),)
