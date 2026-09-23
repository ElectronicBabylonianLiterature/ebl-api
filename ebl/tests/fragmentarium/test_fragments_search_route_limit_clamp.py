import falcon

from ebl.common.query.parameter_parser import MAX_QUERY_LIMIT
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber


def test_query_fragmentarium_limit_above_maximum_is_losslessly_paginated(
    client, fragmentarium
):
    fragments = [
        TransliteratedFragmentFactory.build(number=MuseumNumber.of(f"X.{index}"))
        for index in range(MAX_QUERY_LIMIT + 1)
    ]
    for index, fragment in enumerate(fragments):
        fragmentarium.create(fragment, sort_key=index)

    first = client.simulate_get(
        "/fragments/query",
        params={"limit": str(MAX_QUERY_LIMIT + 1), "count": "page"},
    )
    second = client.simulate_get(
        "/fragments/query",
        params={"limit": str(MAX_QUERY_LIMIT + 1), "offset": MAX_QUERY_LIMIT},
    )
    first_numbers = [item["museumNumber"] for item in first.json["items"]]
    second_numbers = [item["museumNumber"] for item in second.json["items"]]

    assert first.status == second.status == falcon.HTTP_OK
    assert len(first_numbers) == MAX_QUERY_LIMIT
    assert first.json["hasNextPage"] is True
    assert first.json["matchCountTotal"] is None
    assert len(second_numbers) == 1
    assert len(set(map(str, first_numbers + second_numbers))) == MAX_QUERY_LIMIT + 1
