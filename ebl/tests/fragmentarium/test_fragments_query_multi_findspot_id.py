import falcon
import pytest

from ebl.common.domain.scopes import Scope
from ebl.common.query.parameter_parser import (
    MAX_FINDSPOT_ID,
    MAX_FINDSPOT_IDS,
    MAX_FINDSPOT_IDS_RAW_LENGTH,
    parse_findspot_ids,
)
from ebl.common.query.query_result import QueryItem, QueryResult
from ebl.errors import DataError
from ebl.fragmentarium.domain.archaeology import Archaeology
from ebl.fragmentarium.infrastructure.fragment_pattern_matcher import PatternMatcher
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.fragmentarium.fragment_query_test_helpers import (
    query_item_of,
    query_result_of,
)
from ebl.transliteration.domain.museum_number import MuseumNumber


def test_parse_findspot_ids_deduplicates_and_sorts():
    assert parse_findspot_ids({"findspotIds": "3,1,1,2"})["findspotIds"] == [1, 2, 3]


def test_parse_findspot_ids_rejects_malformed():
    with pytest.raises(DataError):
        parse_findspot_ids({"findspotIds": "1,x"})


def test_parse_findspot_ids_rejects_negative():
    with pytest.raises(DataError):
        parse_findspot_ids({"findspotIds": "1,-2"})


def test_parse_findspot_ids_rejects_empty():
    with pytest.raises(DataError):
        parse_findspot_ids({"findspotIds": " , "})


def test_parse_findspot_ids_rejects_over_limit():
    ids = ",".join(str(value) for value in range(MAX_FINDSPOT_IDS + 1))
    with pytest.raises(DataError):
        parse_findspot_ids({"findspotIds": ids})


@pytest.mark.parametrize("value", ["1,,2", ",1", "1,", "1, ,2"])
def test_parse_findspot_ids_rejects_empty_tokens(value):
    with pytest.raises(DataError, match="must not contain empty values"):
        parse_findspot_ids({"findspotIds": value})


@pytest.mark.parametrize("value", ["1_0", "true", "1.0"])
def test_parse_findspot_ids_rejects_non_decimal_values(value):
    with pytest.raises(DataError, match="non-negative decimal integer"):
        parse_findspot_ids({"findspotIds": value})


def test_parse_findspot_ids_rejects_out_of_bson_range():
    with pytest.raises(DataError, match=f"must not exceed {MAX_FINDSPOT_ID}"):
        parse_findspot_ids({"findspotIds": str(MAX_FINDSPOT_ID + 1)})


def test_parse_findspot_ids_rejects_over_raw_length_limit():
    value = "1" * (MAX_FINDSPOT_IDS_RAW_LENGTH + 1)
    with pytest.raises(DataError, match="must not exceed"):
        parse_findspot_ids({"findspotIds": value})


def test_parse_findspot_ids_enforces_combined_limit():
    ids = ",".join(str(value) for value in range(MAX_FINDSPOT_IDS))
    with pytest.raises(DataError, match="must not select more than"):
        parse_findspot_ids({"findspotId": MAX_FINDSPOT_IDS, "findspotIds": ids})


def test_parse_findspot_ids_allows_zero_whitespace_and_bson_max():
    assert parse_findspot_ids({"findspotIds": f" 0, {MAX_FINDSPOT_ID} "})[
        "findspotIds"
    ] == [0, MAX_FINDSPOT_ID]


def test_query_fragmentarium_multiple_findspot_ids(fragment_repository):
    first = FragmentFactory.build(
        number=MuseumNumber.of("X.1"), archaeology=Archaeology(findspot_id=123)
    )
    second = FragmentFactory.build(
        number=MuseumNumber.of("X.2"), archaeology=Archaeology(findspot_id=456)
    )
    other = FragmentFactory.build(
        number=MuseumNumber.of("X.3"), archaeology=Archaeology(findspot_id=789)
    )
    fragment_repository.create_many([first, second, other])

    result = fragment_repository.query({"findspotIds": [123, 456]})

    key = lambda item: str(item.museum_number)  # noqa: E731
    expected_items = sorted(
        [QueryItem(first.number, (), 0), QueryItem(second.number, (), 0)], key=key
    )
    assert QueryResult(sorted(result.items, key=key), result.match_count_total) == (
        QueryResult(expected_items, 0)
    )


def test_search_multiple_findspot_ids(client, fragmentarium):
    matching = FragmentFactory.build(
        number=MuseumNumber.of("X.1"), archaeology=Archaeology(findspot_id=123)
    )
    also_matching = FragmentFactory.build(
        number=MuseumNumber.of("X.2"), archaeology=Archaeology(findspot_id=456)
    )
    non_matching = FragmentFactory.build(
        number=MuseumNumber.of("X.3"), archaeology=Archaeology(findspot_id=789)
    )
    fragmentarium.create(matching)
    fragmentarium.create(also_matching)
    fragmentarium.create(non_matching)

    result = client.simulate_get("/fragments/query", params={"findspotIds": "123,456"})

    assert result.status == falcon.HTTP_OK
    key = lambda item: str(item["museumNumber"])  # noqa: E731
    items = sorted([query_item_of(matching), query_item_of(also_matching)], key=key)
    assert sorted(result.json["items"], key=key) == items


def test_search_findspot_ids_deduplicates_with_single_param(client, fragmentarium):
    matching = FragmentFactory.build(
        number=MuseumNumber.of("X.1"), archaeology=Archaeology(findspot_id=123)
    )
    fragmentarium.create(matching)

    result = client.simulate_get(
        "/fragments/query", params={"findspotId": "123", "findspotIds": "123"}
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of([query_item_of(matching)], 0)


def test_search_findspot_ids_preserves_visibility(client, guest_client, fragmentarium):
    fragment = FragmentFactory.build(
        archaeology=Archaeology(findspot_id=123),
        authorized_scopes=[Scope.READ_ITALIANNINEVEH_FRAGMENTS],
    )
    fragmentarium.create(fragment)

    assert client.simulate_get(
        "/fragments/query", params={"findspotIds": "123,456"}
    ).json == query_result_of([query_item_of(fragment)], 0)
    assert guest_client.simulate_get(
        "/fragments/query", params={"findspotIds": "123,456"}
    ).json == query_result_of([], 0)


@pytest.mark.parametrize(
    "value", ["1,x", "1,-2", " , ", "", "1,,2", ",1", "1,", "1_0", "1.0"]
)
def test_search_findspot_ids_rejects_malformed_values(client, value):
    result = client.simulate_get("/fragments/query", params={"findspotIds": value})

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_search_findspot_ids_rejects_over_limit(client):
    ids = ",".join(str(value) for value in range(MAX_FINDSPOT_IDS + 1))

    result = client.simulate_get("/fragments/query", params={"findspotIds": ids})

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_search_findspot_ids_rejects_out_of_bson_range(client):
    result = client.simulate_get(
        "/fragments/query", params={"findspotIds": str(MAX_FINDSPOT_ID + 1)}
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_findspot_filter_composes_with_metadata_pagination_and_page_count(
    seeded_provenance_service,
):
    pipeline = PatternMatcher(
        {
            "findspotId": 0,
            "findspotIds": [2, 1],
            "scriptPeriod": "Hittite",
            "scriptPeriodModifier": "Early",
            "genre": ["CANONICAL"],
            "offset": 1,
            "limit": 1,
            "count": "page",
        },
        seeded_provenance_service,
    ).build_pipeline()

    assert pipeline[0]["$match"]["$and"][:3] == [
        {"genres.category": {"$all": ["CANONICAL"]}},
        {"script.period": "Hittite", "script.periodModifier": "Early"},
        {"archaeology.findspotId": {"$in": [0, 1, 2]}},
    ]
    items = pipeline[2]["$facet"]["items"]
    assert items[1:3] == [{"$skip": 1}, {"$limit": 2}]
    assert pipeline[3]["$project"]["items"] == {"$slice": ["$items", 1]}
    assert pipeline[3]["$project"]["hasNextPage"] == {"$gt": [{"$size": "$items"}, 1]}
