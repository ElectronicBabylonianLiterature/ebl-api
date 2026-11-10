from dataclasses import dataclass
import json
from threading import Thread
from typing import Sequence, cast
from urllib.request import urlopen
from wsgiref.simple_server import make_server

import falcon
import pytest
from falcon import testing
from pymongo.database import Database

from ebl.fragmentarium.application.fragmentarium import Fragmentarium
from ebl.fragmentarium.application.fragment_query_preview import (
    matching_line_preview_of_data,
)
from ebl.fragmentarium.infrastructure.mongo_fragment_repository import (
    MongoFragmentRepository,
)
from ebl.signs.infrastructure.mongo_sign_repository import MongoSignRepository
from ebl.transliteration.domain.sign import Sign
from ebl.transliteration.domain.museum_number import MuseumNumber

from ebl.fragmentarium.application.fragment_query_summary_schema import (
    FragmentQueryMatchingLinePreviewSchema,
    FragmentQueryPreviewLineSchema,
    FragmentQuerySummarySchema,
)
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.fragmentarium.fragment_query_location_test_helpers import (
    MALFORMED_MARKERS,
    MALFORMED_MARKER_IDS,
)
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
    preview = matching_line_preview_of_data(text, [0, 99])
    assert preview["lines"] == []
    assert preview["totalMatchingLines"] == 0


@dataclass(frozen=True)
class LocationSearch:
    client: testing.TestClient
    database: Database


@pytest.fixture
def location_search(
    client: testing.TestClient,
    fragmentarium: Fragmentarium,
    database: Database,
    sign_repository: MongoSignRepository,
    signs: Sequence[Sign],
) -> LocationSearch:
    for sign in signs:
        sign_repository.create(sign)
    for number in ("X.1", "X.2"):
        fragmentarium.create(
            FragmentFactory.build(
                number=MuseumNumber.of(number),
                text=parse_atf_lark("@obverse\n1. KU\n@reverse\n2. KU"),
                signs="KU\nKU",
            )
        )
    return LocationSearch(client, database)


def query_locations_over_http(client: testing.TestClient) -> dict:
    with make_server("127.0.0.1", 0, client.app) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with urlopen(
                f"http://127.0.0.1:{server.server_port}/fragments/query"
                "?transliteration=KU&limit=2",
                timeout=10,
            ) as response:
                assert response.status == 200
                return cast(dict, json.loads(response.read()))
        finally:
            server.shutdown()
            thread.join(timeout=10)


@pytest.mark.parametrize("transport", ["falcon", "http"])
@pytest.mark.parametrize(
    "marker",
    (*MALFORMED_MARKERS, None),
    ids=(*MALFORMED_MARKER_IDS, "null-stored-line"),
)
def test_malformed_marker_does_not_fail_other_search_results(
    location_search: LocationSearch,
    marker: object,
    transport: str,
) -> None:
    location_search.database["fragments"].update_one(
        {"_id": "X.1"}, {"$set": {"text.lines.2": marker}}
    )
    if transport == "http":
        payload = query_locations_over_http(location_search.client)
    else:
        response = location_search.client.simulate_get(
            "/fragments/query", params={"transliteration": "KU", "limit": "2"}
        )
        assert response.status == falcon.HTTP_OK
        payload = cast(dict, cast(testing.Result, response).json)
    assert len(payload["items"]) == 2
    previews = {
        item["museumNumber"]["number"]: item["matchingLinePreview"]
        for item in payload["items"]
    }
    if marker is None:
        # Mongo's type projection omits the null row; its shifted matching index
        # is skipped, leaving the valid preview before the damaged marker.
        assert [line["index"] for line in previews["1"]["lines"]] == [1]
        assert previews["1"]["lines"][0]["location"]["surface"] == "o"
    else:
        for line in previews["1"]["lines"]:
            assert line["location"] == {
                "surface": None,
                "column": None,
                "object": None,
                "sealNumber": None,
            }
    assert [line["location"]["surface"] for line in previews["2"]["lines"]] == [
        "o",
        "r",
    ]
