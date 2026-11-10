from pathlib import Path

import pytest

from scripts.maps import map_ods_reader
from scripts.maps.map_ods_reader import read_ods_rows
from scripts.maps.map_site_config import SITE_CONFIGS
from scripts.maps.tests.map_ods_test_helpers import write_ods


def test_compact_source_cannot_amplify_text_beyond_the_default_budget(
    tmp_path: Path,
) -> None:
    path = tmp_path / "amplified.ods"
    text = "x" * 4096
    write_ods(
        path,
        '<table:table-row table:number-rows-repeated="10000">'
        f"<table:table-cell><text:p>{text}</text:p></table:table-cell>"
        "</table:table-row>",
    )
    with pytest.raises(ValueError, match="text expansion exceeds"):
        read_ods_rows(path)


@pytest.mark.parametrize(
    "rows",
    [
        (
            '<table:table-row table:number-rows-repeated="2">'
            "<table:table-cell><text:p>abc</text:p></table:table-cell>"
            "</table:table-row>"
        ),
        (
            '<table:table-row><table:table-cell table:number-columns-repeated="2">'
            "<text:p>abc</text:p></table:table-cell></table:table-row>"
        ),
        (
            "<table:table-row><table:table-cell><text:p>abc</text:p>"
            "</table:table-cell></table:table-row>"
        )
        * 2,
    ],
)
def test_expanded_text_budget_covers_rows_columns_and_total_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, rows: str
) -> None:
    monkeypatch.setattr(map_ods_reader, "_MAX_EXPANDED_CHARACTERS", 5)
    path = tmp_path / "repeated.ods"
    write_ods(path, rows)

    with pytest.raises(ValueError, match="text expansion exceeds 5 characters"):
        read_ods_rows(path)


def test_expanded_text_budget_accepts_its_unicode_character_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(map_ods_reader, "_MAX_EXPANDED_CHARACTERS", 4)
    path = tmp_path / "unicode.ods"
    write_ods(
        path,
        '<table:table-row table:number-rows-repeated="2">'
        "<table:table-cell><text:p>𒀭ā</text:p></table:table-cell></table:table-row>",
    )
    assert read_ods_rows(path) == (("𒀭ā",), ("𒀭ā",))


@pytest.mark.parametrize(
    "paragraphs",
    [
        "<text:p>A<text:span>BC</text:span>D</text:p>",
        "<text:p>AB</text:p><text:p>C</text:p>",
    ],
)
def test_cell_text_budget_counts_fragments_and_paragraph_separators_before_join(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, paragraphs: str
) -> None:
    monkeypatch.setattr(map_ods_reader, "_MAX_EXPANDED_CHARACTERS", 3)
    path = tmp_path / "cell.ods"
    write_ods(
        path,
        f"<table:table-row><table:table-cell>{paragraphs}"
        "</table:table-cell></table:table-row>",
    )
    with pytest.raises(ValueError, match="text expansion exceeds"):
        read_ods_rows(path)


@pytest.mark.parametrize(
    "paragraphs",
    [
        "<text:p>A<text:p>B</text:p>C</text:p>",
        "<text:p>A<text:span><text:p>B</text:p></text:span>C</text:p>",
    ],
)
def test_nested_paragraphs_are_rejected_without_duplicate_text(
    tmp_path: Path, paragraphs: str
) -> None:
    path = tmp_path / "nested.ods"
    write_ods(
        path,
        f"<table:table-row><table:table-cell>{paragraphs}"
        "</table:table-cell></table:table-row>",
    )
    with pytest.raises(ValueError, match="paragraphs must not be nested"):
        read_ods_rows(path)


def test_valid_inline_spans_and_list_paragraphs_preserve_text(tmp_path: Path) -> None:
    path = tmp_path / "valid.ods"
    write_ods(
        path,
        "<table:table-row>"
        "<table:table-cell><text:p>A<text:span>B</text:span>C</text:p>"
        "</table:table-cell><table:table-cell><text:list><text:list-item>"
        "<text:p>A</text:p></text:list-item><text:list-item><text:p>B</text:p>"
        "</text:list-item></text:list></table:table-cell></table:table-row>",
    )
    assert read_ods_rows(path) == (("ABC", "A\nB"),)


@pytest.mark.parametrize("site_id", tuple(SITE_CONFIGS))
def test_authoritative_ods_sources_fit_expanded_text_budget(site_id: str) -> None:
    rows = read_ods_rows(SITE_CONFIGS[site_id].ods_path)
    assert rows
    assert sum(len(cell) for row in rows for cell in row) < (
        map_ods_reader._MAX_EXPANDED_CHARACTERS
    )
