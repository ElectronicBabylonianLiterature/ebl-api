import pytest

from ebl.fragmentarium.application.fragment_query_preview import (
    matching_line_preview_of_data,
)
from ebl.fragmentarium.application.fragment_query_locations import locations_of_data
from ebl.tests.fragmentarium.fragment_query_location_test_helpers import (
    MALFORMED_MARKERS,
    MALFORMED_MARKER_IDS,
)
from ebl.tests.fragmentarium.fragment_query_preview_test_helpers import dumped_text
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark


@pytest.mark.parametrize(
    "marker",
    (*MALFORMED_MARKERS, None),
    ids=(*MALFORMED_MARKER_IDS, "null-stored-line"),
)
def test_malformed_markers_leave_text_preview_available_with_unknown_locations(
    marker: object,
) -> None:
    text = dumped_text(parse_atf_lark("@obverse\n1. ku\n@reverse\n2. nu"))
    text["lines"][2] = marker

    preview = matching_line_preview_of_data(text, [1, 3])

    assert preview["totalMatchingLines"] == 2
    assert [line["index"] for line in preview["lines"]] == [1, 3]
    assert [line["prefix"] for line in preview["lines"]] == ["1.", "2."]
    assert all(
        line["location"]
        == {
            "surface": None,
            "column": None,
            "object": None,
            "sealNumber": None,
        }
        for line in preview["lines"]
    )


def test_zero_column_keeps_the_existing_roman_label() -> None:
    assert (
        locations_of_data(
            [
                {"type": "ColumnAtLine", "column_label": {"status": [], "column": 0}},
                {"type": "TextLine"},
            ],
            [1],
        )[1]["column"]
        == "n"
    )
