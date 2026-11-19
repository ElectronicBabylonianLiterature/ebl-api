from pathlib import Path
from zipfile import ZipFile
from unittest.mock import patch

import pytest

from scripts.maps.map_ods_reader import read_ods_rows
from scripts.maps import map_ods_reader
from scripts.maps.tests.map_ods_test_helpers import write_ods as _write_ods


def test_read_ods_rows_expands_rows_cells_and_covered_cells(tmp_path: Path) -> None:
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
) -> None:
    path = tmp_path / "source.ods"
    if "rows" in attribute:
        rows = f"<table:table-row {attribute}><table:table-cell/></table:table-row>"
    else:
        rows = f"<table:table-row><table:table-cell {attribute}/></table:table-row>"
    _write_ods(path, rows)

    with pytest.raises(ValueError, match="repeat"):
        read_ods_rows(path)


def test_read_ods_rows_requires_content_xml(tmp_path: Path) -> None:
    path = tmp_path / "source.ods"
    with ZipFile(path, "w") as archive:
        archive.writestr("other.xml", "<document/>")

    with pytest.raises(ValueError, match="missing content.xml"):
        read_ods_rows(path)


def test_read_ods_rows_limits_xml_before_decompression(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "source.ods"
    _write_ods(path, "<table:table-row/>")
    monkeypatch.setattr(map_ods_reader, "_MAX_XML_BYTES", 1)

    with patch.object(ZipFile, "read", side_effect=AssertionError("must not read")):
        with pytest.raises(ValueError, match="ODS XML exceeds"):
            read_ods_rows(path)


def test_read_ods_rows_requires_a_spreadsheet_body(tmp_path: Path) -> None:
    path = tmp_path / "source.ods"
    with ZipFile(path, "w") as archive:
        archive.writestr("content.xml", "<document/>")

    with pytest.raises(ValueError, match="missing the spreadsheet body"):
        read_ods_rows(path)


def test_read_ods_rows_requires_exactly_one_sheet(tmp_path: Path) -> None:
    path = tmp_path / "source.ods"
    _write_ods(path, "</table:table><table:table>")

    with pytest.raises(ValueError, match="exactly one sheet"):
        read_ods_rows(path)


def test_read_ods_rows_reads_grouped_rows_and_ignores_unrelated_elements(
    tmp_path: Path,
) -> None:
    path = tmp_path / "source.ods"
    _write_ods(
        path,
        """<table:table-header-rows><table:table-row>
<table:unexpected/><table:table-cell><text:p>header</text:p></table:table-cell>
</table:table-row></table:table-header-rows>
<table:table-row-group><table:table-rows><table:table-row/>
</table:table-rows></table:table-row-group><table:unexpected/>""",
    )

    assert read_ods_rows(path) == (("header",), ())


def test_read_ods_rows_limits_combined_cell_repeats(tmp_path: Path) -> None:
    path = tmp_path / "source.ods"
    _write_ods(
        path,
        '<table:table-row><table:table-cell table:number-columns-repeated="16384"/>'
        "<table:table-cell/></table:table-row>",
    )

    with pytest.raises(ValueError, match="ODS row exceeds"):
        read_ods_rows(path)


def test_read_ods_rows_limits_total_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "source.ods"
    _write_ods(path, '<table:table-row table:number-rows-repeated="3"/>')
    monkeypatch.setattr(map_ods_reader, "_MAX_EXPANDED_ROWS", 2)

    with pytest.raises(ValueError, match="ODS row expansion exceeds"):
        read_ods_rows(path)


def test_read_ods_rows_limits_total_expanded_cells(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "source.ods"
    _write_ods(
        path,
        '<table:table-row table:number-rows-repeated="2">'
        '<table:table-cell table:number-columns-repeated="2"/>'
        "</table:table-row>",
    )
    monkeypatch.setattr(map_ods_reader, "_MAX_EXPANDED_CELLS", 4)
    assert read_ods_rows(path) == (("", ""), ("", ""))
    monkeypatch.setattr(map_ods_reader, "_MAX_EXPANDED_CELLS", 3)

    with pytest.raises(ValueError, match="ODS cell expansion exceeds"):
        read_ods_rows(path)
