from typing import Sequence

import pytest

from ebl.fragmentarium.application.fragment_query_locations import (
    advance_location,
    locations_of_data,
)
from ebl.fragmentarium.application.fragment_query_preview import (
    matching_line_preview_of_data,
)
from ebl.tests.fragmentarium.fragment_query_preview_test_helpers import (
    dumped_text,
    numbered_atf,
)
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark
from ebl.transliteration.domain.line_label import LineLabel
from ebl.transliteration.domain.text_line import TextLine


@pytest.mark.parametrize(
    "atf,surface,column,object_label,seal_number",
    [
        ("@obverse\n@column 2\n6. ku", "o", "ii", None, None),
        ("@reverse\n@column 3\n6. ku", "r", "iii", None, None),
        ("@obverse?\n@column 2?\n6-8. ku", "o?", "ii?", None, None),
        ("@column 1\n6. ku", None, "i", None, None),
        ("@obverse\n6. ku", "o", None, None, None),
        ("6. ku", None, None, None, None),
        (
            "@object Stone wig\n@surface face A\n6. ku",
            "face A",
            None,
            "Stone wig",
            None,
        ),
        ("@seal 2\n6. ku", None, None, None, 2),
    ],
)
def test_preview_locations_preserve_domain_labels(
    atf: str,
    surface: str | None,
    column: str | None,
    object_label: str | None,
    seal_number: int | None,
) -> None:
    text = parse_atf_lark(atf)
    index = len(text.lines) - 1
    result = matching_line_preview_of_data(dumped_text(text), [index])
    assert result["lines"][0]["index"] == index
    assert result["lines"][0]["location"] == {
        "surface": surface,
        "column": column,
        "object": object_label,
        "sealNumber": seal_number,
    }
    assert result["totalMatchingLines"] == 1
    assert result["lines"][0]["lineNumber"]["type"] == (
        "LineNumberRange" if "6-8" in atf else "LineNumber"
    )


def test_repeated_line_numbers_follow_original_indexes_and_context() -> None:
    text = parse_atf_lark(
        "@obverse\n@column 1\n6. ku\n@column 2\n6. nu\n@reverse\n6. ku"
    )
    indices = [2, 4, 6]
    result = matching_line_preview_of_data(dumped_text(text), [6, 2, 4, 2])
    assert [line["index"] for line in result["lines"]] == [6, 2, 4]
    assert [line["location"]["surface"] for line in result["lines"]] == ["r", "o", "o"]
    assert [line["location"]["column"] for line in result["lines"]] == ["ii", "i", "ii"]
    assert result["totalMatchingLines"] == len(indices)


def test_location_scanner_agrees_with_complete_text_labels() -> None:
    text = parse_atf_lark(
        "1. ku\n@tablet\n@obverse?\n@column 1\n2. ku\n@seal 3\n"
        "@column 2\n3. ku\n@reverse\n4. ku"
    )
    indices = [
        index for index, line in enumerate(text.lines) if isinstance(line, TextLine)
    ]
    locations = locations_of_data(dumped_text(text)["lines"], indices)
    for label in text.labels:
        assert label.line_index is not None
        assert locations[label.line_index] == {
            "surface": label.surface.to_value() if label.surface else None,
            "column": label.column.to_value() if label.column else None,
            "object": label.object.to_value() if label.object else None,
            "sealNumber": label.seal_number,
        }


def test_omitted_location_markers_and_empty_indexes_are_supported() -> None:
    assert locations_of_data([], []) == {}
    label = LineLabel(None, None, None, None, None)
    assert advance_location(label, parse_atf_lark("1. ku").lines[0]) == label


def test_hidden_matching_lines_do_not_deserialize_unselected_tokens() -> None:
    text = dumped_text(parse_atf_lark(numbered_atf(8)))
    text["lines"][6]["content"] = [{"type": "INVALID_UNSELECTED_TOKEN"}]
    text["lines"].append({"type": "SurfaceAtLine"})
    matching_lines: Sequence[int] = [99, -1, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8]
    result = matching_line_preview_of_data(text, matching_lines)
    assert result["totalMatchingLines"] == 8
    assert [line["index"] for line in result["lines"]] == list(range(5))


def test_late_preview_match_uses_all_preceding_markers() -> None:
    text = parse_atf_lark(
        "@obverse\n" + numbered_atf(40) + "\n@reverse\n@column 2\n41. ku"
    )
    result = matching_line_preview_of_data(dumped_text(text), [43])
    assert result["lines"][0]["location"]["surface"] == "r"
    assert result["lines"][0]["location"]["column"] == "ii"
