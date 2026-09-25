from pathlib import Path
from zipfile import ZipFile

import pytest

from ebl.fragmentarium.application.map_ods_reader import read_ods_rows


def _write_ods(path: Path, rows: str) -> None:
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-content
 xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
 xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">
 <office:body><office:spreadsheet><table:table table:name="Sheet1">
  {rows}
 </table:table></office:spreadsheet></office:body>
</office:document-content>"""
    with ZipFile(path, "w") as archive:
        archive.writestr("content.xml", content)


def test_read_ods_rows_expands_rows_cells_and_covered_cells(tmp_path: Path):
    path = tmp_path / "source.ods"
    _write_ods(
        path,
        """<table:table-row table:number-rows-repeated="2">
 <table:table-cell><text:p>alpha<text:span>beta</text:span>tail</text:p>
  <text:p>next</text:p></table:table-cell>
 <table:covered-table-cell table:number-columns-repeated="2"/>
 <table:table-cell><text:p>last</text:p></table:table-cell>
</table:table-row>""",
    )

    assert read_ods_rows(path) == (
        ("alphabetatail\nnext", "", "", "last"),
        ("alphabetatail\nnext", "", "", "last"),
    )


@pytest.mark.parametrize(
    "attribute",
    [
        'table:number-columns-repeated="16385"',
        'table:number-columns-repeated="invalid"',
        'table:number-rows-repeated="0"',
    ],
)
def test_read_ods_rows_rejects_invalid_or_excessive_repeats(
    tmp_path: Path, attribute: str
):
    path = tmp_path / "source.ods"
    if "rows" in attribute:
        rows = f"<table:table-row {attribute}><table:table-cell/></table:table-row>"
    else:
        rows = f"<table:table-row><table:table-cell {attribute}/></table:table-row>"
    _write_ods(path, rows)

    with pytest.raises(ValueError, match="repeat"):
        read_ods_rows(path)
