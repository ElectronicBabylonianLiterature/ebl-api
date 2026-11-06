from pathlib import Path
import struct

import pytest

from ebl.fragmentarium.application.map_source_reader import (
    load_prj_wkt,
    load_shp_polygon_geometries,
)
from ebl.tests.fragmentarium.map_source_test_helpers import (
    shp_bytes,
    with_declared_length,
)


def _expect_shape_error(tmp_path: Path, contents: bytes, message: str) -> None:
    path = tmp_path / "source.shp"
    path.write_bytes(contents)

    with pytest.raises(ValueError, match=message):
        load_shp_polygon_geometries(path)


@pytest.mark.parametrize(
    "offset, value, message",
    [
        (0, struct.pack(">i", 0), "file code"),
        (28, struct.pack("<i", 999), "version"),
        (32, struct.pack("<i", 3), "Only polygon shapefiles"),
        (100, struct.pack(">i", 2), "record header"),
        (104, struct.pack(">i", 21), "record header"),
        (108, struct.pack("<i", 3), "Only polygon shapefile records"),
        (144, struct.pack("<i", 0), "record dimensions"),
        (148, struct.pack("<i", 3), "record dimensions"),
        (152, struct.pack("<i", 1), "part indexes"),
        (156, struct.pack("<d", float("inf")), "Non-finite"),
    ],
)
def test_shapefile_reader_rejects_invalid_header_record_and_coordinate_values(
    tmp_path: Path, offset: int, value: bytes, message: str
) -> None:
    contents = bytearray(shp_bytes())
    end = offset + len(value)
    contents[offset:end] = value

    _expect_shape_error(tmp_path, bytes(contents), message)


@pytest.mark.parametrize(
    "length, message",
    [(40, "Truncated shapefile header"), (104, "record header"), (-2, "record in")],
)
def test_shapefile_reader_rejects_truncated_payloads_with_consistent_file_length(
    tmp_path: Path, length: int, message: str
) -> None:
    contents = bytearray(shp_bytes()[:length])

    _expect_shape_error(tmp_path, with_declared_length(contents), message)


def test_shapefile_reader_rejects_content_that_disagrees_with_record_dimensions(
    tmp_path: Path,
) -> None:
    contents = bytearray(shp_bytes() + b"\x00\x00")
    contents[104:108] = struct.pack(">i", (len(contents) - 108) // 2)

    _expect_shape_error(tmp_path, with_declared_length(contents), "record dimensions")


@pytest.mark.parametrize("second_part", [0, 10])
def test_shapefile_reader_rejects_nonincreasing_and_out_of_range_parts(
    tmp_path: Path, second_part: int
) -> None:
    first = ((0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0))
    second = ((2.0, 0.0), (2.0, 1.0), (3.0, 1.0), (3.0, 0.0), (2.0, 0.0))
    contents = bytearray(shp_bytes((first, second)))
    contents[156:160] = struct.pack("<i", second_part)

    _expect_shape_error(tmp_path, bytes(contents), "part indexes")


def test_shapefile_reader_rejects_a_short_ring_among_valid_record_dimensions(
    tmp_path: Path,
) -> None:
    short = ((0.0, 0.0), (0.0, 1.0), (0.0, 0.0))
    valid = ((2.0, 0.0), (2.0, 1.0), (3.0, 1.0), (3.0, 0.0), (2.0, 0.0))

    _expect_shape_error(tmp_path, shp_bytes((short, valid)), "unclosed polygon ring")


@pytest.mark.parametrize("contents", [None, b"\xff"])
def test_projection_reader_rejects_missing_and_undecodable_files(
    tmp_path: Path, contents: bytes | None
) -> None:
    path = tmp_path / "source.prj"
    if contents is not None:
        path.write_bytes(contents)

    with pytest.raises(ValueError, match="Cannot read required shapefile CRS"):
        load_prj_wkt(path)


def test_projection_reader_accepts_bom_and_normalizes_surrounding_whitespace(
    tmp_path: Path,
) -> None:
    path = tmp_path / "source.prj"
    path.write_text(' \nGEOGCS["WGS 84"] \n', encoding="utf-8-sig")

    assert load_prj_wkt(path) == 'GEOGCS["WGS 84"]'
