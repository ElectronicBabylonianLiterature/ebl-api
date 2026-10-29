import json

import falcon
import pytest

from ebl.cache.application.cache import DAILY_TIMEOUT, DEFAULT_TIMEOUT
from ebl.sumerian_dictionary.infrastructure.mongo_sumerian_word_repository import (
    MongoSumerianWordRepository,
)
from ebl.sumerian_dictionary.infrastructure.sumerian_word_schemas import (
    SumerianWordSchema,
)
from ebl.tests.factories.sumerian_dictionary import (
    SumerianWordFactory,
    build_complete_word,
)
from ebl.tests.sumerian_dictionary.conftest import InsertWords

ROUTES = (
    "/sumerian-words?query=a",
    "/sumerian-words?ids=a",
    "/sumerian-words/all",
    "/sumerian-words/statistics",
    "/sumerian-words/a",
)


@pytest.mark.parametrize("route", ROUTES)
def test_every_route_requires_the_scope(client, route: str) -> None:
    assert client.simulate_get(route).status == falcon.HTTP_FORBIDDEN


@pytest.mark.parametrize("route", ROUTES)
def test_guests_are_refused(guest_client, route: str) -> None:
    assert guest_client.simulate_get(route).status == falcon.HTTP_FORBIDDEN


def test_get_word(
    reader_client,
    sumerian_word_repository: MongoSumerianWordRepository,
    insert_words: InsertWords,
) -> None:
    word = build_complete_word()
    insert_words(word)

    result = reader_client.simulate_get(f"/sumerian-words/{word.id}")

    assert result.status == falcon.HTTP_OK
    expected = SumerianWordSchema().dump(sumerian_word_repository.find(word.id))
    assert result.json == json.loads(json.dumps(expected))
    assert result.json["_id"] == word.id
    assert result.json["head"] == {
        "id": "o0000001",
        "citationForm": "",
        "homonym": "",
        "guideWord": "",
    }


def test_get_missing_word(reader_client) -> None:
    result = reader_client.simulate_get("/sumerian-words/sux-000001")

    assert result.status == falcon.HTTP_NOT_FOUND
    assert result.json["description"] == "Sumerian word 'sux-000001' not found."


def test_list_ids(reader_client, insert_words: InsertWords) -> None:
    insert_words(SumerianWordFactory.build(id="o2"), SumerianWordFactory.build(id="o1"))

    result = reader_client.simulate_get("/sumerian-words/all")

    assert result.status == falcon.HTTP_OK
    assert sorted(result.json) == ["o1", "o2"]
    assert result.headers["Cache-Control"] == f"private, max-age={DEFAULT_TIMEOUT}"
    assert result.headers["Age"] == "0"


def test_list_ids_is_memoised(cached_reader_client, insert_words: InsertWords) -> None:
    insert_words(SumerianWordFactory.build(id="o1"))
    first = cached_reader_client.simulate_get("/sumerian-words/all")
    insert_words(SumerianWordFactory.build(id="o2"))

    second = cached_reader_client.simulate_get("/sumerian-words/all")

    assert first.json == second.json == ["o1"]


def test_statistics(reader_client, insert_words: InsertWords) -> None:
    insert_words(SumerianWordFactory.build(pos="DN"))

    result = reader_client.simulate_get("/sumerian-words/statistics")

    assert result.status == falcon.HTTP_OK
    assert result.json == {
        "lemmas": 1,
        "attinger": 1,
        "aligned": 0,
        "epsd2Only": 0,
        "properNouns": 1,
        "withAkkadian": 0,
    }
    assert result.headers["Cache-Control"] == f"private, max-age={DAILY_TIMEOUT}"
    assert result.headers["Age"] == "0"


def test_statistics_are_memoised(
    cached_reader_client, insert_words: InsertWords
) -> None:
    first = cached_reader_client.simulate_get("/sumerian-words/statistics")
    insert_words(SumerianWordFactory.build())

    second = cached_reader_client.simulate_get("/sumerian-words/statistics")

    assert first.json == second.json
    assert second.json["lemmas"] == 0
