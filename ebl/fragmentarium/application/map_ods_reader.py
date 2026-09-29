from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

_ODS_NAMESPACES = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
}
_COLUMN_REPEAT_KEY = "{%s}number-columns-repeated" % _ODS_NAMESPACES["table"]
_ROW_REPEAT_KEY = "{%s}number-rows-repeated" % _ODS_NAMESPACES["table"]
_CELL_TAG = "{%s}table-cell" % _ODS_NAMESPACES["table"]
_COVERED_CELL_TAG = "{%s}covered-table-cell" % _ODS_NAMESPACES["table"]
_ROW_TAG = "{%s}table-row" % _ODS_NAMESPACES["table"]
_ROW_CONTAINER_TAGS = {
    "{%s}table-header-rows" % _ODS_NAMESPACES["table"],
    "{%s}table-row-group" % _ODS_NAMESPACES["table"],
    "{%s}table-rows" % _ODS_NAMESPACES["table"],
}
_MAX_COLUMN_REPEAT = 16_384
_MAX_ROW_REPEAT = 10_000
_MAX_EXPANDED_ROWS = 100_000


def read_ods_rows(path: Path) -> tuple[tuple[str, ...], ...]:
    with ZipFile(path) as archive:
        root = ET.fromstring(archive.read("content.xml"))
    spreadsheet = root.find("office:body/office:spreadsheet", _ODS_NAMESPACES)
    if spreadsheet is None:
        raise ValueError(f"{path} is missing the spreadsheet body.")
    tables = spreadsheet.findall("table:table", _ODS_NAMESPACES)
    if len(tables) != 1:
        raise ValueError(f"Expected exactly one sheet in {path}.")
    rows: list[tuple[str, ...]] = []
    for row in _table_rows(tables[0]):
        expanded = tuple(_expand_row(row))
        repeat = _repeat(row, _ROW_REPEAT_KEY, "row", _MAX_ROW_REPEAT)
        if len(rows) + repeat > _MAX_EXPANDED_ROWS:
            raise ValueError(f"ODS row expansion exceeds {_MAX_EXPANDED_ROWS} rows.")
        rows.extend([expanded] * repeat)
    return tuple(rows)


def _table_rows(container: ET.Element):
    for child in container:
        if child.tag == _ROW_TAG:
            yield child
        elif child.tag in _ROW_CONTAINER_TAGS:
            yield from _table_rows(child)


def _expand_row(row: ET.Element) -> list[str]:
    values: list[str] = []
    for cell in row:
        if cell.tag not in (_CELL_TAG, _COVERED_CELL_TAG):
            continue
        repeat = _repeat(cell, _COLUMN_REPEAT_KEY, "column", _MAX_COLUMN_REPEAT)
        if len(values) + repeat > _MAX_COLUMN_REPEAT:
            raise ValueError(f"ODS row exceeds {_MAX_COLUMN_REPEAT} columns.")
        text = "" if cell.tag == _COVERED_CELL_TAG else _cell_text(cell)
        values.extend([text] * repeat)
    return values


def _repeat(element: ET.Element, key: str, kind: str, maximum: int) -> int:
    raw_repeat = element.attrib.get(key, "1")
    try:
        repeat = int(raw_repeat)
    except ValueError as error:
        raise ValueError(f"Invalid ODS {kind} repeat {raw_repeat!r}.") from error
    if not 1 <= repeat <= maximum:
        raise ValueError(f"ODS {kind} repeat must be between 1 and {maximum}.")
    return repeat


def _cell_text(cell: ET.Element) -> str:
    paragraphs = cell.findall(".//text:p", _ODS_NAMESPACES)
    return "\n".join("".join(paragraph.itertext()) for paragraph in paragraphs)
