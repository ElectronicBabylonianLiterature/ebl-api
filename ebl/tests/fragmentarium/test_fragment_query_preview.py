import pytest

from ebl.fragmentarium.application.fragment_query_preview import (
    matching_line_preview_of,
    preview_line_of,
)
from ebl.tests.fragmentarium.fragment_query_preview_test_helpers import (
    COMPLEX_ATF,
    PREVIEW_LINE_FIELDS,
    dumped,
)
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark


@pytest.fixture
def complex_line():
    return parse_atf_lark(COMPLEX_ATF).lines[0]


@pytest.fixture
def complex_preview(complex_line):
    return preview_line_of(0, dumped(complex_line))


def test_preview_line_carries_only_the_compact_fields(complex_preview):
    assert set(complex_preview) == PREVIEW_LINE_FIELDS


def test_preview_line_omits_the_detail_representation(complex_line):
    detail = dumped(complex_line)
    preview = preview_line_of(0, detail)

    assert "content" in detail
    assert "lineNumber" in detail
    assert "content" not in preview
    assert "lineNumber" not in preview
    assert "type" not in preview


def test_preview_keeps_compact_fields(complex_preview):
    assert complex_preview["number"] == "1'."
    assert complex_preview["prefix"] == "1'."
    assert complex_preview["text"] == "[ku]-nu-uš KUR# {d}INANA ⸢ki⸣ %sux gu-du/gu₂"


def test_preview_keeps_every_token_type(complex_preview):
    assert [token["type"] for token in complex_preview["tokens"]] == [
        "Word",
        "Word",
        "Word",
        "Word",
        "LanguageShift",
        "Word",
    ]


def test_preview_keeps_token_values_and_clean_values(complex_preview):
    assert [token["value"] for token in complex_preview["tokens"]] == [
        "[ku]-nu-uš",
        "KUR#",
        "{d}INANA",
        "⸢ki⸣",
        "%sux",
        "gu-du/gu₂",
    ]
    assert complex_preview["tokens"][0]["cleanValue"] == "ku-nu-uš"
    assert complex_preview["tokens"][1]["cleanValue"] == "KUR"


def test_preview_token_omits_empty_unique_lemma(complex_preview):
    assert all("uniqueLemma" not in token for token in complex_preview["tokens"])


def test_preview_token_keeps_a_present_unique_lemma():
    preview = preview_line_of(
        0, {"prefix": "1.", "content": [{"value": "ku", "uniqueLemma": ["ku I"]}]}
    )

    assert preview["tokens"] == [{"value": "ku", "uniqueLemma": ["ku I"]}]


def test_preview_keeps_a_line_number_range_as_the_number():
    line = parse_atf_lark("1-2. ku-nu-uš").lines[0]
    preview = preview_line_of(0, dumped(line))

    assert preview["number"] == "1-2."
    assert preview["prefix"] == "1-2."


def test_preview_keeps_the_compact_shape_for_a_non_text_line():
    text = parse_atf_lark("1. ku\n$ (end of side)")
    preview = matching_line_preview_of(text, (1, 7))

    assert len(preview["lines"]) == 1
    assert set(preview["lines"][0]) == PREVIEW_LINE_FIELDS
    assert preview["lines"][0]["number"] == "$"
    assert preview["lines"][0]["text"] == " end of side"


def test_preview_of_a_line_without_content():
    assert preview_line_of(2, {"prefix": "1."}) == {
        "index": 2,
        "number": "1.",
        "prefix": "1.",
        "text": "",
        "tokens": [],
    }
