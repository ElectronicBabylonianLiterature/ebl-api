import pytest

from ebl.fragmentarium.application.fragment_query_preview import (
    MAX_PREVIEW_LINES,
    matching_line_preview_of_data,
)
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.fragmentarium.fragment_query_preview_test_helpers import (
    COMPLEX_ATF,
    dumped_text,
    matching_line_preview_of,
    numbered_atf,
)
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark


@pytest.fixture
def long_text():
    return parse_atf_lark(numbered_atf(30))


def test_preview_of_stored_data_matches_domain_preview():
    fragment = FragmentFactory.build(text=parse_atf_lark(COMPLEX_ATF))

    assert (
        matching_line_preview_of_data(dumped_text(fragment), (0,))["lines"]
        == matching_line_preview_of(fragment.text, (0,))["lines"]
    )


def test_data_builder_uses_the_wire_key_and_domain_builder_the_attribute_name():
    fragment = FragmentFactory.build(text=parse_atf_lark("1. ku"))
    version = fragment.text.parser_version

    assert (
        matching_line_preview_of_data(dumped_text(fragment), (0,))["parserVersion"]
        == version
    )
    assert matching_line_preview_of(fragment.text, (0,))["parser_version"] == version


def test_the_two_builders_differ_only_in_the_parser_version_key():
    fragment = FragmentFactory.build(text=parse_atf_lark("1. ku"))
    from_data = matching_line_preview_of_data(dumped_text(fragment), (0,))
    from_domain = matching_line_preview_of(fragment.text, (0,))

    assert set(from_data) == {"lines", "parserVersion"}
    assert set(from_domain) == {"lines", "parser_version"}
    assert from_data["lines"] == from_domain["lines"]


def test_preview_serializes_only_selected_lines():
    text = parse_atf_lark(numbered_atf(20))
    preview = matching_line_preview_of(text, (0, 4))

    assert len(text.lines) == 20
    assert [line["prefix"] for line in preview["lines"]] == ["1.", "5."]


def test_preview_carries_the_source_index_of_each_line():
    text = parse_atf_lark(numbered_atf(20))
    preview = matching_line_preview_of(text, (0, 4, 11))

    assert [line["index"] for line in preview["lines"]] == [0, 4, 11]
    assert [line["prefix"] for line in preview["lines"]] == ["1.", "5.", "12."]


def test_preview_index_survives_deduplication_and_capping(long_text):
    preview = matching_line_preview_of(long_text, (99, 3, 3, 1, 7, 7, 2, 9, 4))

    assert [line["index"] for line in preview["lines"]] == [3, 1, 7, 2, 9]


def test_stored_data_preview_carries_the_same_indexes():
    fragment = FragmentFactory.build(text=parse_atf_lark(numbered_atf(20, "ku")))
    matching_lines = (5, 2, 5, 8)

    assert [
        line["index"]
        for line in matching_line_preview_of_data(
            dumped_text(fragment), matching_lines
        )["lines"]
    ] == [5, 2, 8]


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

    assert [line["prefix"] for line in preview["lines"]] == [
        f"{index}." for index in range(1, MAX_PREVIEW_LINES + 1)
    ]


def test_preview_cap_skips_out_of_range_before_capping(long_text):
    preview = matching_line_preview_of(long_text, (99, 0, 1, 2, 3, 4, 5))

    assert [line["prefix"] for line in preview["lines"]] == [
        f"{index}." for index in range(1, MAX_PREVIEW_LINES + 1)
    ]


@pytest.mark.parametrize(
    "matching_lines,expected_numbers",
    [
        ((0, 1, 1, 2, 2, 3), ["1.", "2.", "3.", "4."]),
        ((0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5), ["1.", "2.", "3.", "4.", "5."]),
        ((3, 1, 3, 2, 1, 4), ["4.", "2.", "3.", "5."]),
        ((99, 0, 0, 1, 2, 3, 4, 5), ["1.", "2.", "3.", "4.", "5."]),
    ],
)
def test_preview_deduplicates_matching_indexes(
    long_text, matching_lines, expected_numbers
):
    preview = matching_line_preview_of(long_text, matching_lines)

    assert [line["prefix"] for line in preview["lines"]] == expected_numbers


def test_stored_data_preview_applies_the_same_cap():
    fragment = FragmentFactory.build(text=parse_atf_lark(numbered_atf(30, "ku")))
    matching_lines = tuple(range(30))
    lines = matching_line_preview_of_data(dumped_text(fragment), matching_lines)[
        "lines"
    ]

    assert lines == matching_line_preview_of(fragment.text, matching_lines)["lines"]
    assert len(lines) == MAX_PREVIEW_LINES


def test_stored_data_preview_deduplicates_the_same_way():
    fragment = FragmentFactory.build(text=parse_atf_lark(numbered_atf(30, "ku")))
    matching_lines = (0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5)

    assert (
        matching_line_preview_of_data(dumped_text(fragment), matching_lines)["lines"]
        == matching_line_preview_of(fragment.text, matching_lines)["lines"]
    )
