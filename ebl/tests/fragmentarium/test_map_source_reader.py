from pathlib import Path
import struct

import pytest

from ebl.fragmentarium.application.map_dbf_reader import (
    load_dbf_encoding,
    load_dbf_rows,
)
from ebl.fragmentarium.application.map_source_reader import (
    load_prj_wkt,
    load_shp_polygon_geometries,
)
from ebl.tests.fragmentarium.map_source_test_helpers import dbf_bytes, shp_bytes


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
    path.write_bytes(dbf_bytes())

    assert load_dbf_rows(path, "ascii") == ({"Name": "Room"},)


@pytest.mark.parametrize(
    "contents, message",
    [
        (dbf_bytes()[:20], "header"),
        (dbf_bytes()[:-3], "record"),
        (dbf_bytes(trailing=b"junk"), "trailing"),
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
    path.write_bytes(shp_bytes())

    assert load_shp_polygon_geometries(path) == (
        ((((43.0, 35.0), (43.0, 35.1), (43.1, 35.1), (43.0, 35.0)),),),
    )


@pytest.mark.parametrize(
    "mutation, message", [("length", "length"), ("truncated", "length")]
)
def test_load_shp_polygon_geometries_rejects_inexact_file_structure(
    tmp_path: Path, mutation: str, message: str
):
    contents = bytearray(shp_bytes())
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
        shp_bytes(
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
    path.write_bytes(shp_bytes((hole, second, exterior)))

    assert load_shp_polygon_geometries(path) == (((second,), (exterior, hole)),)
