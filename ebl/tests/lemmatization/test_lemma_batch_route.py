from typing import Callable, List, Sequence, Tuple

import falcon
import pytest
from falcon import testing
from pymongo.collection import Collection
from pymongo.database import Database

from ebl.dictionary.application.dictionary_service import (
    COLLECTION as WORDS_COLLECTION,
)
from ebl.tests.corpus.lines_edit_support import read_json
from ebl.tests.lemmatization.lemma_batch_support import (
    BATCH_URL,
    EXPECTED_LEMMAS,
    QUERIES,
    Query,
    create_body,
    find_entry_lemma_ids,
    find_lemma_ids,
    get_lemmas,
    post_batch,
    read_entries,
    read_lemmas,
)

RecordedQuery = Tuple[str, str]
MISSING_WORD_ID = "ana II"
MALFORMED_BODIES: Sequence[Tuple[object, Sequence[str]]] = (
    ({}, ["words"]),
    ({"words": None}, ["words"]),
    ({"words": "ana"}, ["words"]),
    ({"words": []}, ["words"]),
    ({"words": ["ana"]}, ["words"]),
    ({"words": [{}]}, ["words"]),
    ({"words": [{"word": "ana"}]}, ["words"]),
    ({"words": [{"isNormalized": True}]}, ["words"]),
    ({"words": [{"word": 1, "isNormalized": True}]}, ["words"]),
    ({"words": [{"word": None, "isNormalized": True}]}, ["words"]),
    ({"words": [{"word": ["ana"], "isNormalized": True}]}, ["words"]),
    ({"words": [{"word": "ana", "isNormalized": "true"}]}, ["words"]),
    ({"words": [{"word": "ana", "isNormalized": 1}]}, ["words"]),
    ({"words": [{"word": "ana", "isNormalized": 0}]}, ["words"]),
    ({"words": [{"word": "ana", "isNormalized": None}]}, ["words"]),
    ({"words": [{"word": "ana", "isNormalized": True, "id": 1}]}, ["words"]),
    ({"words": create_body([("ana", True)] * 201)["words"]}, ["words"]),
    ({**create_body(QUERIES), "limit": 1}, ["limit"]),
    ({"word": "ana", "isNormalized": True}, ["isNormalized", "word", "words"]),
    ([], ["_schema"]),
    (None, ["_schema"]),
    ("ana", ["_schema"]),
)


@pytest.fixture
def recorded_queries(monkeypatch: pytest.MonkeyPatch) -> List[RecordedQuery]:
    queries: List[RecordedQuery] = []

    def record(method: str) -> None:
        query: Callable[..., object] = getattr(Collection, method)

        def query_and_record(
            collection: Collection, *args: object, **kwargs: object
        ) -> object:
            queries.append((collection.name, method))
            return query(collection, *args, **kwargs)

        monkeypatch.setattr(Collection, method, query_and_record)

    for method in ("aggregate", "find", "find_one"):
        record(method)
    return queries


def test_batch_equals_the_single_searches_in_request_order(
    client: testing.TestClient, seeded_lemmas: None
) -> None:
    result = post_batch(client, create_body(QUERIES))

    assert result.status == falcon.HTTP_OK
    assert result.json == [
        {
            "word": word,
            "isNormalized": is_normalized,
            "lemmas": get_lemmas(client, (word, is_normalized)).json,
        }
        for word, is_normalized in QUERIES
    ]


def test_batch_finds_the_lemmas_of_fragments_and_chapters(
    client: testing.TestClient, seeded_lemmas: None
) -> None:
    result = post_batch(client, create_body(QUERIES))

    assert find_entry_lemma_ids(result) == [list(lemmas) for lemmas in EXPECTED_LEMMAS]


@pytest.mark.parametrize("query", dict.fromkeys(QUERIES))
def test_batch_of_one_word_equals_the_single_search(
    client: testing.TestClient, seeded_lemmas: None, query: Query
) -> None:
    result = post_batch(client, create_body([query]))

    assert result.status == falcon.HTTP_OK
    assert [entry["lemmas"] for entry in read_entries(result)] == [
        get_lemmas(client, query).json
    ]


@pytest.mark.parametrize(
    "queries,expected",
    [
        (QUERIES, [("fragments", "aggregate")] * 2 + [("words", "aggregate")]),
        (
            [query for query in QUERIES if not query[1]],
            [("fragments", "aggregate"), ("words", "aggregate")],
        ),
        ([("absent", True)], [("fragments", "aggregate"), ("words", "aggregate")]),
    ],
)
def test_batch_queries_the_database_once_per_flag_and_once_for_the_dictionary(
    client: testing.TestClient,
    seeded_lemmas: None,
    recorded_queries: List[RecordedQuery],
    queries: Sequence[Query],
    expected: Sequence[RecordedQuery],
) -> None:
    result = post_batch(client, create_body(queries))

    assert result.status == falcon.HTTP_OK
    assert recorded_queries == expected


def test_batch_of_the_maximum_size(
    client: testing.TestClient, seeded_lemmas: None
) -> None:
    queries = [(f"ana{index}", False) for index in range(199)]

    result = post_batch(client, create_body([*queries, ("ana", False)]))

    assert result.status == falcon.HTTP_OK
    assert [entry["word"] for entry in read_entries(result)] == [
        *(word for word, _ in queries),
        "ana",
    ]
    assert find_entry_lemma_ids(result)[-1] == list(EXPECTED_LEMMAS[0])


def test_missing_dictionary_word_is_reported_like_the_single_search(
    client: testing.TestClient, seeded_lemmas: None, database: Database
) -> None:
    database[WORDS_COLLECTION].delete_one({"_id": MISSING_WORD_ID})

    result = post_batch(client, create_body(QUERIES))
    single_result = get_lemmas(client, QUERIES[0])

    assert result.status == single_result.status == falcon.HTTP_NOT_FOUND
    assert result.json == single_result.json


def test_guest_can_search(
    guest_client: testing.TestClient, seeded_lemmas: None
) -> None:
    result = post_batch(guest_client, create_body(QUERIES))

    assert result.status == falcon.HTTP_OK
    assert find_entry_lemma_ids(result) == [list(lemmas) for lemmas in EXPECTED_LEMMAS]


@pytest.mark.parametrize("body,invalid_fields", MALFORMED_BODIES)
def test_malformed_body(
    client: testing.TestClient,
    recorded_queries: List[RecordedQuery],
    body: object,
    invalid_fields: Sequence[str],
) -> None:
    result = post_batch(client, body)

    assert result.status == falcon.HTTP_BAD_REQUEST
    assert read_json(result)["title"] == "Request data failed validation"
    assert sorted(read_json(result)["description"]) == invalid_fields
    assert recorded_queries == []


@pytest.mark.parametrize("body", ["", "{", '{"words": ['])
def test_invalid_json(client: testing.TestClient, body: str) -> None:
    result = client.simulate_post(BATCH_URL, body=body)

    assert result.status == falcon.HTTP_BAD_REQUEST


def test_getting_the_batch_route_is_not_allowed(client: testing.TestClient) -> None:
    result = client.simulate_get(BATCH_URL)

    assert result.status == falcon.HTTP_METHOD_NOT_ALLOWED


def test_single_search_is_still_routed(
    client: testing.TestClient, seeded_lemmas: None
) -> None:
    result = get_lemmas(client, QUERIES[0])

    assert result.status == falcon.HTTP_OK
    assert find_lemma_ids(read_lemmas(result)) == list(EXPECTED_LEMMAS[0])
