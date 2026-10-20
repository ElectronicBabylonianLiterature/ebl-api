import zipfile
from pathlib import Path

import pytest

from ebl.tests.provenance.kmz_test_helpers import (
    POINT,
    POINT_XML,
    POLYGON_XML,
    kml_bytes,
    placemark,
    record,
)
from scripts import import_kmz_coordinates as cli


def test_name_normalization_and_regions() -> None:
    assert cli.normalize_name("  Aššur’ ? ") == "assur"
    assert cli.basic_name_key(" Aššur? ") == "aššur"
    assert cli.extract_name_variants("Assur / Aššur (Aššur / Assur?)") == (
        "Assur",
        "Aššur",
    )
    assert cli.is_broad_region_name("Northern Babylonia")
    assert cli.is_broad_region_record(record("Unrecognized", "SUMER"))
    assert not cli.is_broad_region_record(record())


@pytest.mark.parametrize("coordinate", ["43", "x,35", "43,nan", "181,35"])
def test_invalid_coordinates_are_rejected(coordinate: str) -> None:
    with pytest.raises(ValueError):
        cli.parse_kml_coordinate(coordinate)


def test_closed_coordinates_and_altitude() -> None:
    assert cli.parse_kml_coordinate("43,35,100") == POINT
    assert cli.parse_kml_coordinate_sequence("43,35 44,36 43,35") == (
        POINT,
        {"latitude": 36.0, "longitude": 44.0},
    )


@pytest.mark.parametrize(
    "name,geometry,reason",
    [
        ("Sumer", POINT_XML, "non-site KMZ placemark"),
        (
            "Assur",
            "<Point><coordinates>x,35</coordinates></Point>",
            "invalid KMZ coordinate",
        ),
        ("Assur", "<Point />", "missing KMZ coordinate"),
        (
            "Assur",
            "<Polygon><coordinates>43,35 44,36</coordinates></Polygon>",
            "invalid KMZ coordinate",
        ),
        (
            "Assur",
            "<Polygon><coordinates> </coordinates></Polygon>",
            "missing KMZ coordinate",
        ),
        ("Assur", "<LineString />", "LineString-only placemark"),
        ("", "<description>none</description>", "unsupported geometry"),
    ],
)
def test_unusable_placemarks(name: str, geometry: str, reason: str) -> None:
    parsed = placemark(name, geometry)
    assert parsed.ignored_reason == reason
    assert not parsed.has_usable_geometry


def test_multiple_geometries_preserve_valid_geometry() -> None:
    parsed = placemark(
        geometry="<Point/><Polygon/>" + POINT_XML + POLYGON_XML + "<LineString />"
    )
    assert parsed.geometry_type == "Point+Polygon+LineString"
    assert parsed.point == POINT
    assert len(parsed.polygon) == 3
    assert parsed.has_usable_point and parsed.has_usable_polygon


def test_unnamed_placemark_is_preserved() -> None:
    parsed = cli.parse_kml_bytes(b"<kml><Placemark /></kml>")
    assert parsed.placemarks[0].raw_name == "<unnamed placemark>"


def test_load_kml_and_missing_input(tmp_path: Path) -> None:
    path = tmp_path / "source.KML"
    path.write_bytes(kml_bytes())
    parsed = cli.parse_kmz(path)
    assert parsed.kml_file_name == "source.KML"
    assert parsed.placemarks[0].point == POINT
    with pytest.raises(FileNotFoundError):
        cli.parse_kmz(tmp_path / "absent.kml")


@pytest.mark.parametrize("preferred", ["doc.kml", "a.kml"])
def test_archive_selection(tmp_path: Path, preferred: str) -> None:
    path = tmp_path / "source.kmz"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("b.kml", kml_bytes("Other"))
        archive.writestr(preferred, kml_bytes())
        archive.writestr("ignore.kml/", b"")
    assert cli.parse_kmz(path).placemarks[0].raw_name == "Assur"


def test_archive_without_kml_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "empty.kmz"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("readme.txt", "not KML")
    with pytest.raises(ValueError, match="No KML"):
        cli.parse_kmz(path)
