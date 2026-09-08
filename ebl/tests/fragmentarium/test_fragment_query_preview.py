import pytest

from ebl.fragmentarium.application.fragment_query_preview import preview_line_of
from ebl.tests.fragmentarium.fragment_query_preview_test_helpers import (
    COMPLEX_ATF,
    PREVIEW_LINE_FIELDS,
    dumped,
    matching_line_preview_of,
)
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark


@pytest.fixture
def complex_line():
    return parse_atf_lark(COMPLEX_ATF).lines[0]


@pytest.fixture
def complex_preview(complex_line):
    return preview_line_of(0, dumped(complex_line))


def test_preview_line_carries_the_full_line_and_the_source_index(complex_preview):
    assert set(complex_preview) == PREVIEW_LINE_FIELDS
    assert complex_preview["index"] == 0
    assert complex_preview["type"] == "TextLine"


def test_preview_line_preserves_the_detail_representation(complex_line):
    detail = dumped(complex_line)
    preview = preview_line_of(0, detail)

    assert preview["content"] == detail["content"]
    assert preview["lineNumber"] == detail["lineNumber"]
    assert preview["prefix"] == detail["prefix"]


def test_preview_line_keeps_the_full_tokens_including_nested_parts(complex_preview):
    assert [token["type"] for token in complex_preview["content"]] == [
        "Word",
        "Word",
        "Word",
        "Word",
        "LanguageShift",
        "Word",
    ]
    assert complex_preview["content"][0]["parts"]


def test_preview_line_keeps_a_line_number_range():
    line = parse_atf_lark("1-2. ku-nu-uš").lines[0]
    preview = preview_line_of(0, dumped(line))

    assert preview["lineNumber"]["type"] == "LineNumberRange"
    assert preview["prefix"] == "1-2."


def test_preview_excludes_non_text_lines():
    text = parse_atf_lark("1. ku\n$ (end of side)")
    preview = matching_line_preview_of(text, (0, 1))

    assert [line["prefix"] for line in preview["lines"]] == ["1."]
    assert all(line["type"] == "TextLine" for line in preview["lines"])


def test_preview_of_a_line_without_extra_fields():
    line = {"type": "TextLine", "prefix": "1.", "content": []}

    assert preview_line_of(2, line) == {**line, "index": 2}
