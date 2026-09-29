import math
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


def _mutated_shp(offset: int, replacement: bytes) -> bytes:
    contents = bytearray(shp_bytes())
    end = offset + len(replacement)
    contents[offset:end] = replacement
    return bytes(contents)


def _extended_shp(extra: bytes) -> bytes:
    return with_declared_length(bytearray(shp_bytes() + extra))


def test_load_prj_wkt_rejects_unreadable_file(tmp_path: Path):
    with pytest.raises(ValueError, match="Cannot read"):
        load_prj_wkt(tmp_path / "missing.prj")


@pytest.mark.parametrize(
    "contents, message",
    [
        (shp_bytes()[:50], "Truncated shapefile header"),
        (_mutated_shp(0, struct.pack(">i", 1)), "Invalid shapefile file code"),
        (_mutated_shp(28, struct.pack("<i", 1001)), "Unsupported shapefile version"),
        (_mutated_shp(32, struct.pack("<i", 1)), "Only polygon shapefiles"),
        (_extended_shp(b"\x00\x00\x00\x02"), "Truncated shapefile record header"),
        (_mutated_shp(100, struct.pack(">i", 2)), "Invalid shapefile record header"),
        (_mutated_shp(104, struct.pack(">i", 21)), "Invalid shapefile record header"),
        (_mutated_shp(104, struct.pack(">i", 999)), "Truncated shapefile record"),
        (_mutated_shp(108, struct.pack("<i", 1)), "Only polygon shapefile records"),
        (_mutated_shp(144, struct.pack("<i", 0)), "Invalid polygon record dimensions"),
        (_mutated_shp(148, struct.pack("<i", 3)), "Invalid polygon record dimensions"),
        (_mutated_shp(152, struct.pack("<i", 1)), "Invalid polygon part indexes"),
        (_mutated_shp(156, struct.pack("<d", math.nan)), "Non-finite polygon"),
    ],
)
def test_load_shp_polygon_geometries_rejects_invalid_structure(
    tmp_path: Path, contents: bytes, message: str
):
    path = tmp_path / "source.shp"
    path.write_bytes(contents)

    with pytest.raises(ValueError, match=message):
        load_shp_polygon_geometries(path)


def test_load_shp_polygon_geometries_rejects_unordered_part_indexes(
    tmp_path: Path,
):
    ring = ((0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (0.0, 0.0))
    contents = bytearray(shp_bytes((ring, ring)))
    contents[156:160] = struct.pack("<i", 0)
    path = tmp_path / "source.shp"
    path.write_bytes(bytes(contents))

    with pytest.raises(ValueError, match="Invalid polygon part indexes"):
        load_shp_polygon_geometries(path)
