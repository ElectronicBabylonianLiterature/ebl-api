from typing import Sequence, cast

import falcon
import pytest
from falcon import testing

from ebl.fragmentarium.application.fragmentarium import Fragmentarium
from ebl.fragmentarium.infrastructure.mongo_fragment_repository import (
    MongoFragmentRepository,
)
from ebl.signs.infrastructure.mongo_sign_repository import MongoSignRepository
from ebl.transliteration.domain.sign import Sign

from ebl.fragmentarium.application.fragment_query_summary_schema import (
    FragmentQueryMatchingLinePreviewSchema,
    FragmentQueryPreviewLineSchema,
    FragmentQuerySummarySchema,
)
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.fragmentarium.fragment_query_test_helpers import query_summary_of
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark


def test_multiline_overlaps_count_distinct_lines_and_keep_occurrence_count(
    fragment_repository: MongoFragmentRepository,
) -> None:
    text = parse_atf_lark(
        "@obverse\n@column 2\n" + "\n".join(f"{index}. ku" for index in range(1, 8))
    )
    fragment_repository.create(
        FragmentFactory.build(text=text, signs="\n".join(["KU"] * 7))
    )
    result = fragment_repository.query({"transliteration": ["KU", "KU"], "limit": 1})
    item = result.items[0]
    assert result.match_count_total == item.match_count == 6
    assert len(item.matching_lines) == 12
    preview = cast(dict, FragmentQuerySummarySchema().dump(item))["matchingLinePreview"]
    assert preview["totalMatchingLines"] == 7
    assert len(preview["lines"]) == 5
    assert preview["totalMatchingLines"] - len(preview["lines"]) == 2
    assert [line["index"] for line in preview["lines"]] == list(range(2, 7))
    assert all(line["location"]["surface"] == "o" for line in preview["lines"])
    assert all(line["location"]["column"] == "ii" for line in preview["lines"])


def test_locations_are_serialized_on_the_existing_query_route(
    client: testing.TestClient,
    fragmentarium: Fragmentarium,
    sign_repository: MongoSignRepository,
    signs: Sequence[Sign],
) -> None:
    for sign in signs:
        sign_repository.create(sign)
    fragment = FragmentFactory.build(
        text=parse_atf_lark("@reverse\n@column 2?\n6-8. KU"), signs="KU"
    )
    fragmentarium.create(fragment)
    response = client.simulate_get(
        "/fragments/query", params={"transliteration": "KU", "limit": "1"}
    )
    assert response.status == falcon.HTTP_OK
    payload = cast(dict, cast(testing.Result, response).json)
    preview = payload["items"][0]["matchingLinePreview"]
    assert preview["totalMatchingLines"] == 1
    line = preview["lines"][0]
    assert line["index"] == 2
    assert line["location"] == {
        "surface": "r",
        "column": "ii?",
        "object": None,
        "sealNumber": None,
    }
    assert line["lineNumber"]["type"] == "LineNumberRange"


def test_old_preview_payload_does_not_invent_location_or_line_count() -> None:
    fragment = FragmentFactory.build(text=parse_atf_lark("6. ku"))
    preview = query_summary_of(fragment, [0])["matchingLinePreview"]
    preview.pop("totalMatchingLines")
    line = preview["lines"][0]
    line.pop("location")
    line_schema = FragmentQueryPreviewLineSchema()
    assert line_schema.dump(line_schema.load(line)) == line
    preview_schema = FragmentQueryMatchingLinePreviewSchema()
    assert preview_schema.dump(preview_schema.load(preview)) == preview


@pytest.mark.parametrize("text", [{}, {"lines": None}])
def test_legacy_missing_text_has_exact_zero_matching_lines(text: dict) -> None:
    from ebl.fragmentarium.application.fragment_query_preview import (
        matching_line_preview_of_data,
    )

    preview = matching_line_preview_of_data(text, [0, 99])
    assert preview["lines"] == []
    assert preview["totalMatchingLines"] == 0
