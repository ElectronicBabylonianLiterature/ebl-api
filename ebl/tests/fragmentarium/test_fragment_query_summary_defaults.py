from typing import cast

import pytest

from ebl.fragmentarium.application.fragment_query_summary_schema import (
    FragmentQueryArchaeologySchema,
    FragmentQuerySummarySchema,
)
from ebl.fragmentarium.domain.fragment_query_summary import (
    FragmentQueryArchaeology,
    FragmentQueryResult,
    FragmentQuerySummary,
    empty_matching_line_preview,
)
from ebl.fragmentarium.infrastructure.mongo_fragment_repository_get_summary import (
    fragment_photo_filename,
)
from ebl.fragmentarium.infrastructure.mongo_fragment_repository_pipelines import (
    filter_fragment_lines,
    omit_text_lines,
)
from ebl.tests.factories.fragment import FragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber


def summary_payload(**overrides) -> dict:
    return {
        "museumNumber": {"prefix": "K", "number": "1", "suffix": ""},
        "description": "",
        "script": {"period": "NA", "periodModifier": "None", "uncertain": False},
        "matchingLines": [],
        "matchCount": 0,
        "hasPhoto": False,
        **overrides,
    }


@pytest.mark.parametrize("site", [None, ""])
def test_archaeology_schema_deserializes_an_absent_site_as_none(site):
    archaeology = cast(
        FragmentQueryArchaeology,
        FragmentQueryArchaeologySchema().load({"site": site}),
    )

    assert archaeology.site is None


@pytest.mark.parametrize("preview", [None, "absent"])
def test_summary_without_a_preview_falls_back_to_the_empty_preview(preview):
    payload = summary_payload()
    if preview is not None:
        payload["matchingLinePreview"] = None

    summary = cast(FragmentQuerySummary, FragmentQuerySummarySchema().load(payload))

    assert summary.matching_line_preview == empty_matching_line_preview()
    assert "parser_version" in summary.matching_line_preview
    assert "parserVersion" not in summary.matching_line_preview


def test_empty_query_result_has_no_items_and_no_matches():
    result = FragmentQueryResult.create_empty()

    assert result.items == []
    assert result.match_count_total == 0
    assert result.bibliography_documents == {}


def test_photo_filename_of_a_museum_number_object():
    assert fragment_photo_filename(MuseumNumber("K", "1", "a")) == "K.1.a.jpg"


@pytest.mark.parametrize(
    "museum_number,expected",
    [
        ({"prefix": "K", "number": "1", "suffix": ""}, "K.1.jpg"),
        ({"prefix": "K", "number": "1", "suffix": "a"}, "K.1.a.jpg"),
    ],
)
def test_photo_filename_of_a_stored_museum_number(museum_number, expected):
    assert fragment_photo_filename(museum_number) == expected


def test_omit_text_lines_blanks_the_lines_field():
    assert omit_text_lines() == [{"$addFields": {"text.lines": []}}]


def test_filter_fragment_lines_without_lines_is_a_no_op():
    assert filter_fragment_lines(None) == []
    assert filter_fragment_lines([]) == []


def test_filter_fragment_lines_maps_the_requested_indexes():
    assert filter_fragment_lines([1, 3]) == [
        {
            "$addFields": {
                "text.lines": {
                    "$map": {
                        "input": [1, 3],
                        "as": "i",
                        "in": {"$arrayElemAt": ["$text.lines", "$$i"]},
                    }
                }
            }
        }
    ]


@pytest.mark.parametrize("data", [None, {}])
def test_loading_a_query_result_without_data_gives_the_empty_result(
    fragment_repository, data
):
    assert fragment_repository._load_fragment_query_result(data) == (
        FragmentQueryResult.create_empty()
    )


def test_query_museum_numbers_matches_the_prefix_and_number_pattern(
    fragment_repository,
):
    for number in ("K.1", "K.2", "X.1"):
        fragment_repository.create(
            FragmentFactory.build(number=MuseumNumber.of(number))
        )

    found = fragment_repository.query_museum_numbers("K", "^[0-9]+$")

    assert sorted(document["museumNumber"]["number"] for document in found) == [
        "1",
        "2",
    ]
