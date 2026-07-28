from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
import struct
import unicodedata
from xml.etree import ElementTree as ET
from zipfile import ZipFile


ASSUR_ODS_PATH = Path("Maps/Assur LRZ/Assur Tafeln.ods")
ASSUR_SHP_BASE = Path("Maps/Assur LRZ/Findspots/Findspots")
ASSUR_SITE_ID = "ASSUR"
ASSUR_SITE_NAME = "Aššur"

_ODS_NAMESPACES = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
}
_EXPECTED_HEADER = ("_id", "area", "sector", "site", "map")


@dataclass(frozen=True)
class AssurOdsRow:
    findspot_id: int
    area: str
    sector: str
    site_name: str
    map_name: str


@dataclass(frozen=True)
class AssurPolygon:
    name: str
    area_name: str
    polygon_id: str
    geometry_checksum: str


def load_assur_ods_rows(path: Path = ASSUR_ODS_PATH) -> tuple[AssurOdsRow, ...]:
    with ZipFile(path) as archive:
        root = ET.fromstring(archive.read("content.xml"))
    spreadsheet = root.find("office:body/office:spreadsheet", _ODS_NAMESPACES)
    if spreadsheet is None:
        raise ValueError("Aššur ODS is missing the spreadsheet body.")
    tables = spreadsheet.findall("table:table", _ODS_NAMESPACES)
    if len(tables) != 1:
        raise ValueError("Expected exactly one sheet in the Aššur ODS.")
    rows = [
        _expand_ods_row(row)
        for row in tables[0].findall("table:table-row", _ODS_NAMESPACES)
    ]
    header = tuple(rows[0][: len(_EXPECTED_HEADER)])
    if header != _EXPECTED_HEADER:
        raise ValueError(f"Unexpected ODS header: {header!r}")
    return tuple(
        AssurOdsRow(
            findspot_id=int(values[0]),
            area=values[1].strip(),
            sector=values[2].strip(),
            site_name=values[3].strip(),
            map_name=values[4].strip(),
        )
        for values in rows[1:]
        if values and values[0].strip()
    )


def load_assur_polygons(base_path: Path = ASSUR_SHP_BASE) -> tuple[AssurPolygon, ...]:
    encoding = _load_dbf_encoding(base_path.with_suffix(".cpg"))
    attributes = _load_dbf_rows(base_path.with_suffix(".dbf"), encoding)
    geometry_rows = _load_shp_rings(base_path.with_suffix(".shp"))
    prj = base_path.with_suffix(".prj").read_text(encoding="utf-8").strip()
    if "WGS_1984" not in prj:
        raise ValueError("Unexpected CRS in the Aššur shapefile.")
    if len(attributes) != len(geometry_rows):
        raise ValueError("Shapefile geometry and DBF row counts differ.")
    polygons = tuple(
        _build_polygon(attribute["Name"], rings)
        for attribute, rings in zip(attributes, geometry_rows, strict=True)
    )
    if len({polygon.name for polygon in polygons}) != len(polygons):
        raise ValueError("Aššur shapefile polygon names must be unique.")
    if len({polygon.polygon_id for polygon in polygons}) != len(polygons):
        raise ValueError("Aššur polygon IDs must be unique.")
    return polygons


def normalize_assur_area_label(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip().replace("?", "")
    return re.sub(r"\s+", " ", normalized).casefold()


def shapefile_area_name(name: str) -> str:
    return re.sub(r"^\d+", "", unicodedata.normalize("NFKC", name).strip())


def build_assur_polygon_id(
    name: str, rings: tuple[tuple[tuple[float, float], ...], ...]
) -> tuple[str, str]:
    slug = re.sub(
        r"[^a-z0-9]+",
        "-",
        unicodedata.normalize("NFKC", name).casefold(),
    ).strip("-")
    if not slug:
        slug = "u" + "-".join(f"{ord(character):04x}" for character in name)
    checksum = hashlib.sha1(_canonical_geometry(rings).encode("utf-8")).hexdigest()[:12]
    return f"assur-{slug}-{checksum}", checksum


def _build_polygon(
    name: str, rings: tuple[tuple[tuple[float, float], ...], ...]
) -> AssurPolygon:
    if _contains_control_character(name):
        raise ValueError(f"Aššur polygon name contains a control character: {name!r}")
    polygon_id, checksum = build_assur_polygon_id(name, rings)
    return AssurPolygon(
        name=name,
        area_name=shapefile_area_name(name),
        polygon_id=polygon_id,
        geometry_checksum=checksum,
    )


def _contains_control_character(value: str) -> bool:
    return any(unicodedata.category(character) == "Cc" for character in value)


def _expand_ods_row(row: ET.Element) -> list[str]:
    values: list[str] = []
    for cell in row.findall("table:table-cell", _ODS_NAMESPACES):
        repeat_key = "{%s}number-columns-repeated" % _ODS_NAMESPACES["table"]
        repeat = int(cell.attrib.get(repeat_key, "1"))
        text = "".join(
            part for element in cell.iter() for part in [element.text] if part
        )
        values.extend([text] * repeat)
    return values


def _load_dbf_encoding(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip() if path.exists() else "latin1"


def _load_dbf_rows(path: Path, encoding: str) -> tuple[dict[str, str], ...]:
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


def _load_shp_rings(
    path: Path,
) -> tuple[tuple[tuple[tuple[float, float], ...], ...], ...]:
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
                    for start, end in zip(
                        part_bounds[:-1], part_bounds[1:], strict=True
                    )
                )
            )
    return tuple(rings_by_feature)


def _canonical_geometry(rings: tuple[tuple[tuple[float, float], ...], ...]) -> str:
    canonical_rings = sorted(_serialize_ring(_canonical_ring(ring)) for ring in rings)
    if not canonical_rings:
        raise ValueError("Polygon must contain at least one ring.")
    return "|".join(canonical_rings)


def _canonical_ring(
    ring: tuple[tuple[float, float], ...],
) -> tuple[tuple[float, float], ...]:
    if len(ring) < 4 or ring[0] != ring[-1]:
        raise ValueError("Polygon rings must be explicitly closed.")
    vertices = ring[:-1]
    if len(set(vertices)) < 3:
        raise ValueError("Polygon rings must contain at least three distinct points.")
    clockwise = _best_rotation(vertices)
    counter_clockwise = _best_rotation(tuple(reversed(vertices)))
    best = min(clockwise, counter_clockwise, key=_serialize_ring)
    return best + (best[0],)


def _best_rotation(
    vertices: tuple[tuple[float, float], ...],
) -> tuple[tuple[float, float], ...]:
    return min(
        (vertices[index:] + vertices[:index] for index in range(len(vertices))),
        key=_serialize_ring,
    )


def _serialize_ring(ring: tuple[tuple[float, float], ...]) -> str:
    return ";".join(f"{_format_coordinate(x)},{_format_coordinate(y)}" for x, y in ring)


def _format_coordinate(value: float) -> str:
    return format(value, ".15f").rstrip("0").rstrip(".")
