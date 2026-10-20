from __future__ import annotations

import zipfile
from pathlib import Path
from xml.etree import ElementTree

from scripts.kmz.geometry import (
    _direct_child_text,
    _extract_point,
    _extract_polygon,
    _geometry_type,
    _iter,
)
from scripts.kmz.models import KmlParseResult, KmlPlacemark
from scripts.kmz.names import (
    extract_name_variants,
    is_broad_region_name,
    normalize_spaces,
)


def parse_kmz(path: Path | str) -> KmlParseResult:
    kmz_path = Path(path)
    if not kmz_path.exists():
        raise FileNotFoundError(f"KMZ/KML file not found: {kmz_path}")

    if kmz_path.suffix.casefold() == ".kml":
        return parse_kml_bytes(kmz_path.read_bytes(), str(kmz_path), kmz_path.name)

    with zipfile.ZipFile(kmz_path) as archive:
        kml_names = [
            name
            for name in archive.namelist()
            if name.casefold().endswith(".kml") and not name.endswith("/")
        ]
        if not kml_names:
            raise ValueError(f"No KML file found inside KMZ: {kmz_path}")
        kml_file_name = next(
            (name for name in kml_names if Path(name).name.casefold() == "doc.kml"),
            sorted(kml_names)[0],
        )
        return parse_kml_bytes(
            archive.read(kml_file_name), str(kmz_path), kml_file_name
        )


def parse_kml_bytes(
    kml_bytes: bytes, kmz_path: str = "<memory>", kml_file_name: str = "doc.kml"
) -> KmlParseResult:
    root = ElementTree.fromstring(kml_bytes)
    placemarks = tuple(
        parse_placemark(placemark) for placemark in _iter(root, "Placemark")
    )
    return KmlParseResult(kmz_path, kml_file_name, placemarks)


def parse_placemark(placemark: ElementTree.Element) -> KmlPlacemark:
    raw_name = normalize_spaces(_direct_child_text(placemark, "name") or "")
    if not raw_name:
        raw_name = "<unnamed placemark>"

    point, point_invalid, point_missing = _extract_point(placemark)
    polygon, polygon_invalid, polygon_missing = _extract_polygon(placemark)
    has_line_string = any(True for _ in _iter(placemark, "LineString"))
    geometry_type = _geometry_type(point, polygon, has_line_string)

    ignored_reason = None
    if is_broad_region_name(raw_name):
        ignored_reason = "non-site KMZ placemark"
    elif not point and not polygon:
        if point_invalid or polygon_invalid:
            ignored_reason = "invalid KMZ coordinate"
        elif point_missing or polygon_missing:
            ignored_reason = "missing KMZ coordinate"
        elif has_line_string:
            ignored_reason = "LineString-only placemark"
        else:
            ignored_reason = "unsupported geometry"

    return KmlPlacemark(
        raw_name=raw_name,
        variants=extract_name_variants(raw_name),
        geometry_type=geometry_type,
        point=point,
        polygon=polygon,
        ignored_reason=ignored_reason,
    )
