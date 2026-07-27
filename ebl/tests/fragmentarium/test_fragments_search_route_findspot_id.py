import falcon
import pytest

from ebl.common.domain.scopes import Scope
from ebl.fragmentarium.domain.archaeology import Archaeology
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.fragmentarium.fragment_query_test_helpers import (
    query_item_of,
    query_result_of,
)
from ebl.transliteration.domain.museum_number import MuseumNumber


def test_search_findspot_id(client, fragmentarium):
    matching = FragmentFactory.build(
        number=MuseumNumber.of("X.1"),
        archaeology=Archaeology(findspot_id=123),
    )
    fragmentarium.create(matching)
    fragmentarium.create(
        FragmentFactory.build(
            number=MuseumNumber.of("X.2"),
            archaeology=Archaeology(findspot_id=456),
        )
    )

    result = client.simulate_get("/fragments/query", params={"findspotId": "123"})

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of([query_item_of(matching)], 0)


def test_search_findspot_id_preserves_visibility(client, guest_client, fragmentarium):
    fragment = FragmentFactory.build(
        archaeology=Archaeology(findspot_id=123),
        authorized_scopes=[Scope.READ_ITALIANNINEVEH_FRAGMENTS],
    )
    fragmentarium.create(fragment)

    assert client.simulate_get(
        "/fragments/query", params={"findspotId": "123"}
    ).json == query_result_of([query_item_of(fragment)], 0)
    assert guest_client.simulate_get(
        "/fragments/query", params={"findspotId": "123"}
    ).json == query_result_of([], 0)


@pytest.mark.parametrize("value", ["invalid", "-1"])
def test_search_findspot_id_rejects_invalid_values(client, value):
    result = client.simulate_get("/fragments/query", params={"findspotId": value})

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
