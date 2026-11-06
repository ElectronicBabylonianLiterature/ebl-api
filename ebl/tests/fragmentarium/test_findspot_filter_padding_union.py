from typing import cast

import falcon
from falcon import testing

from ebl.common.query.parameter_parser import parse_findspot_ids
from ebl.fragmentarium.application.fragmentarium import Fragmentarium
from ebl.fragmentarium.domain.archaeology import Archaeology
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.fragmentarium.fragment_query_test_helpers import (
    query_item_of,
    query_result_of,
)
from ebl.transliteration.domain.museum_number import MuseumNumber


def test_parse_findspot_ids_accepts_padded_values() -> None:
    assert parse_findspot_ids({"findspotIds": "0" * 63 + "1,0002"})["findspotIds"] == [
        1,
        2,
    ]


def test_search_findspot_ids_preserves_distinct_single_selection(
    client: testing.TestClient, fragmentarium: Fragmentarium
) -> None:
    matching = FragmentFactory.build(
        number=MuseumNumber.of("X.1"), archaeology=Archaeology(findspot_id=123)
    )
    also_matching = FragmentFactory.build(
        number=MuseumNumber.of("X.2"), archaeology=Archaeology(findspot_id=456)
    )
    fragmentarium.create(matching)
    fragmentarium.create(also_matching)

    result = cast(
        testing.Result,
        client.simulate_get(
            "/fragments/query", params={"findspotId": "123", "findspotIds": "456,456"}
        ),
    )

    assert result.status == falcon.HTTP_OK
    payload = cast(dict, result.json)
    assert {
        **payload,
        "items": sorted(payload["items"], key=lambda item: str(item["museumNumber"])),
    } == query_result_of([query_item_of(matching), query_item_of(also_matching)], 0)
