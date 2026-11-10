import falcon
import pytest

from ebl.tests.corpus.corpus_query_route_fixtures import (
    CHAPTER_WITH_LEMMA,
    CHAPTER_WITH_SIGNS,
    CHAPTER_WITH_SIGNS_AND_LEMMAS,
    query_response_of,
)


@pytest.mark.parametrize(
    "params,expected",
    [
        ({"lemmaOperator": "and", "lemmas": "ina I+qanû I"}, ([0, 1], [0, 0])),
        ({"lemmaOperator": "or", "lemmas": "ginâ I+bamātu I+mu I"}, ([1, 2], [0, 0])),
        ({"lemmaOperator": "line", "lemmas": "mu I+u I"}, ([2], [0])),
        ({"lemmaOperator": "phrase", "lemmas": "mu I+u I"}, ([2], [0])),
    ],
    ids=["and", "or", "line", "phrase"],
)
def test_query_chapter_lemmas(client, text_repository, params, expected):
    text_repository.create_chapter(CHAPTER_WITH_LEMMA)

    result = client.simulate_get("/corpus/query", params=params)

    assert result.status == falcon.HTTP_OK
    assert result.json == query_response_of(CHAPTER_WITH_LEMMA, *expected)


@pytest.mark.usefixtures("registered_sign_repository")
@pytest.mark.parametrize(
    "transliteration,expected",
    [
        ("bul bansur", ([0], [0])),
        ("ti", ([2, 3], [1, 0])),
        ("x", ([0, 2, 3], [0, 1, 0])),
        ("šu", ([2], [1])),
        ("ma šu\nba", ([2, 3], [1, 0])),
    ],
)
def test_query_chapter_signs(client, text_repository, transliteration, expected):
    text_repository.create_chapter(CHAPTER_WITH_SIGNS)

    result = client.simulate_get(
        "/corpus/query",
        params={"transliteration": transliteration},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_response_of(CHAPTER_WITH_SIGNS, *expected)


@pytest.mark.usefixtures("registered_sign_repository")
@pytest.mark.parametrize(
    "params,expected",
    [
        (
            {
                "transliteration": "bul bansur",
                "lemmas": "ina I",
                "lemmaOperator": "and",
            },
            ([0, 4], [0, 0]),
        ),
        (
            {
                "transliteration": "ma šu\nba",
                "lemmas": "bamātu I+qanû I",
                "lemmaOperator": "phrase",
            },
            ([2, 3, 5], [1, 0, 0]),
        ),
        (
            {"transliteration": "ti", "lemmas": "u I+mu I", "lemmaOperator": "line"},
            ([2, 3, 6], [1, 0, 0]),
        ),
    ],
    ids=["and", "phrase", "line"],
)
def test_query_chapter_lemmas_and_signs(client, text_repository, params, expected):
    text_repository.create_chapter(CHAPTER_WITH_SIGNS_AND_LEMMAS)

    result = client.simulate_get("/corpus/query", params=params)

    assert result.status == falcon.HTTP_OK
    assert result.json == query_response_of(CHAPTER_WITH_SIGNS_AND_LEMMAS, *expected)
