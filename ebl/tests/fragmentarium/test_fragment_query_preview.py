import pytest

from ebl.fragmentarium.application.fragment_query_preview import (
    MAX_PREVIEW_LINES,
    matching_line_preview_of,
    matching_line_preview_of_data,
    preview_line_of,
)
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.tests.factories.fragment import FragmentFactory
from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark

COMPLEX_ATF = "1'. [ku]-nu-uš KUR# {d}INANA ⸢ki⸣ %sux gu-du/gu₂"


@pytest.fixture
def complex_line():
    return parse_atf_lark(COMPLEX_ATF).lines[0]


def word_of(line: dict, index: int) -> dict:
    return line["content"][index]


def test_preview_line_matches_detail_line_serialization(complex_line):
    detail = OneOfLineSchema().dump(complex_line)
    preview = preview_line_of(detail)

    assert preview["type"] == detail["type"]
    assert preview["prefix"] == detail["prefix"]
    assert preview["lineNumber"] == detail["lineNumber"]
    assert preview["content"] == detail["content"]


def test_preview_keeps_compact_fields(complex_line):
    preview = preview_line_of(OneOfLineSchema().dump(complex_line))

    assert preview["number"] == "1'."
    assert preview["text"] == "[ku]-nu-uš KUR# {d}INANA ⸢ki⸣ %sux gu-du/gu₂"
    assert [token["type"] for token in preview["tokens"]] == [
        "Word",
        "Word",
        "Word",
        "Word",
        "LanguageShift",
        "Word",
    ]


def test_preview_line_number_matches_detail_representation(complex_line):
    preview = preview_line_of(OneOfLineSchema().dump(complex_line))

    assert preview["lineNumber"] == {
        "number": 1,
        "hasPrime": True,
        "prefixModifier": None,
        "suffixModifier": None,
        "type": "LineNumber",
    }


def test_preview_keeps_ordinary_reading(complex_line):
    preview = preview_line_of(OneOfLineSchema().dump(complex_line))
    reading = word_of(preview, 0)["parts"][1]

    assert reading["type"] == "Reading"
    assert reading["name"] == "ku"
    assert reading["nameParts"][0]["value"] == "ku"


def test_preview_keeps_logogram_and_flags(complex_line):
    preview = preview_line_of(OneOfLineSchema().dump(complex_line))
    logogram = word_of(preview, 1)["parts"][0]

    assert logogram["type"] == "Logogram"
    assert logogram["flags"] == ["#"]


def test_preview_keeps_determinative_parts(complex_line):
    preview = preview_line_of(OneOfLineSchema().dump(complex_line))
    determinative = word_of(preview, 2)["parts"][0]

    assert determinative["type"] == "Determinative"
    assert [part["type"] for part in determinative["parts"]] == ["Reading"]


def test_preview_keeps_enclosure_metadata(complex_line):
    preview = preview_line_of(OneOfLineSchema().dump(complex_line))
    parts = word_of(preview, 0)["parts"]

    assert parts[0] == {
        "value": "[",
        "cleanValue": "",
        "enclosureType": [],
        "erasure": "NONE",
        "side": "LEFT",
        "type": "BrokenAway",
    }
    assert parts[1]["enclosureType"] == ["BROKEN_AWAY"]
    assert parts[2]["side"] == "RIGHT"


def test_preview_keeps_language_shift(complex_line):
    preview = preview_line_of(OneOfLineSchema().dump(complex_line))
    shift = word_of(preview, 4)

    assert shift["type"] == "LanguageShift"
    assert shift["language"] == "SUMERIAN"


def test_preview_keeps_nested_variant(complex_line):
    preview = preview_line_of(OneOfLineSchema().dump(complex_line))
    variant = word_of(preview, 5)["parts"][2]

    assert variant["type"] == "Variant"
    assert [token["type"] for token in variant["tokens"]] == ["Reading", "Reading"]


def test_preview_of_stored_data_matches_domain_preview():
    fragment = FragmentFactory.build(text=parse_atf_lark(COMPLEX_ATF))
    stored = FragmentSchema(exclude=["joins"]).dump(fragment)

    assert (
        matching_line_preview_of_data(stored["text"], (0,))["lines"]
        == (matching_line_preview_of(fragment.text, (0,))["lines"])
    )


def test_preview_serializes_only_selected_lines():
    text = parse_atf_lark("\n".join(f"{index}. ku-nu-uš" for index in range(1, 21)))
    preview = matching_line_preview_of(text, (0, 4))

    assert len(text.lines) == 20
    assert [line["number"] for line in preview["lines"]] == ["1.", "5."]


@pytest.fixture
def long_text():
    return parse_atf_lark("\n".join(f"{index}. ku-nu-uš" for index in range(1, 31)))


@pytest.mark.parametrize(
    "matching_count,expected",
    [
        (0, 0),
        (1, 1),
        (MAX_PREVIEW_LINES - 1, MAX_PREVIEW_LINES - 1),
        (MAX_PREVIEW_LINES, MAX_PREVIEW_LINES),
        (MAX_PREVIEW_LINES + 1, MAX_PREVIEW_LINES),
        (30, MAX_PREVIEW_LINES),
    ],
)
def test_preview_caps_line_count(long_text, matching_count, expected):
    preview = matching_line_preview_of(long_text, tuple(range(matching_count)))

    assert len(preview["lines"]) == expected


def test_preview_cap_keeps_the_first_matching_lines_in_order(long_text):
    preview = matching_line_preview_of(long_text, tuple(range(30)))

    assert [line["number"] for line in preview["lines"]] == [
        f"{index}." for index in range(1, MAX_PREVIEW_LINES + 1)
    ]


def test_preview_cap_skips_out_of_range_before_capping(long_text):
    preview = matching_line_preview_of(long_text, (99, 0, 1, 2, 3, 4, 5))

    assert [line["number"] for line in preview["lines"]] == [
        f"{index}." for index in range(1, MAX_PREVIEW_LINES + 1)
    ]


def test_stored_data_preview_applies_the_same_cap():
    fragment = FragmentFactory.build(
        text=parse_atf_lark("\n".join(f"{index}. ku" for index in range(1, 31)))
    )
    stored = FragmentSchema(exclude=["joins"]).dump(fragment)
    matching_lines = tuple(range(30))

    assert (
        matching_line_preview_of_data(stored["text"], matching_lines)["lines"]
        == matching_line_preview_of(fragment.text, matching_lines)["lines"]
    )
    assert (
        len(matching_line_preview_of_data(stored["text"], matching_lines)["lines"])
        == MAX_PREVIEW_LINES
    )


def test_preview_keeps_line_number_range():
    line = parse_atf_lark("1-2. ku-nu-uš").lines[0]
    preview = preview_line_of(OneOfLineSchema().dump(line))

    assert preview["lineNumber"]["type"] == "LineNumberRange"
    assert preview["lineNumber"] == OneOfLineSchema().dump(line)["lineNumber"]
    assert preview["number"] == "1-2."


def test_preview_skips_out_of_range_and_empty_content():
    text = parse_atf_lark("1. ku\n$ (end of side)")
    preview = matching_line_preview_of(text, (1, 7))

    assert len(preview["lines"]) == 1
    assert preview["lines"][0]["type"] == "StateDollarLine"
    assert "lineNumber" not in preview["lines"][0]
