from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

_ODS_NAMESPACES = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
}
_REPEAT_KEY = "{%s}number-columns-repeated" % _ODS_NAMESPACES["table"]


def read_ods_rows(path: Path) -> tuple[tuple[str, ...], ...]:
    with ZipFile(path) as archive:
        root = ET.fromstring(archive.read("content.xml"))
    spreadsheet = root.find("office:body/office:spreadsheet", _ODS_NAMESPACES)
    if spreadsheet is None:
        raise ValueError(f"{path} is missing the spreadsheet body.")
    tables = spreadsheet.findall("table:table", _ODS_NAMESPACES)
    if len(tables) != 1:
        raise ValueError(f"Expected exactly one sheet in {path}.")
    return tuple(
        tuple(_expand_row(row))
        for row in tables[0].findall("table:table-row", _ODS_NAMESPACES)
    )


def _expand_row(row: ET.Element) -> list[str]:
    values: list[str] = []
    for cell in row.findall("table:table-cell", _ODS_NAMESPACES):
        repeat = int(cell.attrib.get(_REPEAT_KEY, "1"))
        text = "".join(
            part for element in cell.iter() for part in [element.text] if part
        )
        values.extend([text] * repeat)
    return values
