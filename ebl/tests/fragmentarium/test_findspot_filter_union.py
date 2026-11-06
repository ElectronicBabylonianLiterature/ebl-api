from typing import cast

import falcon
from falcon import testing
import pytest

from ebl.common.query.parameter_parser import parse_findspot_ids
from ebl.fragmentarium.application.fragmentarium import Fragmentarium
from ebl.fragmentarium.domain.archaeology import Archaeology
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.fragmentarium.fragment_query_test_helpers import (
    query_item_of,
)
from ebl.transliteration.domain.museum_number import MuseumNumber


def test_search_findspot_ids_unions_distinct_single_and_plural_ids(
    client: testing.TestClient, fragmentarium: Fragmentarium
) -> None:
    matching = [
        FragmentFactory.build(
            number=MuseumNumber.of(f"X.{index}"),
            archaeology=Archaeology(findspot_id=findspot_id),
        )
        for index, findspot_id in enumerate((123, 456), start=1)
    ]
    for fragment in matching:
        fragmentarium.create(fragment)
    result = cast(
        testing.Result,
        client.simulate_get(
            "/fragments/query", params={"findspotId": "123", "findspotIds": "456"}
        ),
    )

    assert result.status == falcon.HTTP_OK
    items = cast(dict, result.json)["items"]
    assert sorted(items, key=str) == sorted(
        [query_item_of(fragment) for fragment in matching], key=str
    )


@pytest.mark.parametrize("value", ["0" * 63 + "1", "0" * 64])
def test_plural_findspot_ids_accept_zero_padding_within_raw_limit(value: str) -> None:
    assert parse_findspot_ids({"findspotIds": value})["findspotIds"] == [int(value)]
