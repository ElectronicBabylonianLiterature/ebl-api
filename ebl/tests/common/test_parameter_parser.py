import pytest
import re
from ebl.common.query.parameter_parser import (
    parse_integer_field,
    parse_pages,
    parse_lemmas,
    parse_lines,
    parse_transliteration,
    parse_genre,
)
from ebl.common.query.query_result import LemmaQueryType
from ebl.errors import DataError
from ebl.transliteration.application.transliteration_query_factory import (
    TransliterationQueryFactory,
)
from pydash import flow


PARAMS = {
    "limit": "42",
    "pages": "3",
    "bibId": "author123",
    "lemmas": "first I+second II",
    "lemmaOperator": "or",
    "transliteration": "me lik\nkur",
}


def test_parse_integer_field():
    parse = parse_integer_field("limit")
    assert parse(PARAMS) == {**PARAMS, "limit": 42}


def test_parse_integer_field_invalid():
    parse = parse_integer_field("invalid_field")
    with pytest.raises(
        DataError, match="invalid_field must be integer, got 'not an int' instead"
    ):
        parse({"invalid_field": "not an int"})


def test_parse_pages():
    assert parse_pages(PARAMS) == {**PARAMS, "pages": "3"}


def test_parse_pages_missing_id():
    with pytest.raises(DataError, match="Name, Year or Title required"):
        parse_pages({"pages": "123"})


@pytest.mark.parametrize(
    "lemmas,lemma_operator,expected_operator",
    [
        ("single I", "line", LemmaQueryType.AND),
        ("foo I+bar II", "and", LemmaQueryType.AND),
        ("foo I+bar II", "or", LemmaQueryType.OR),
        ("foo I+bar II", "line", LemmaQueryType.LINE),
        ("foo I+bar II", "phrase", LemmaQueryType.PHRASE),
    ],
)
def test_parse_lemmas(lemmas: str, lemma_operator: str, expected_operator):
    expected = {
        "lemmas": lemmas.split("+"),
        "lemmaOperator": expected_operator,
    }
    assert parse_lemmas({"lemmas": lemmas, "lemmaOperator": lemma_operator}) == expected


def test_parse_lemmas_invalid():
    with pytest.raises(DataError, match="unexpected lemmaOperator 'wrong operator'"):
        parse_lemmas({"lemmas": "foo I+bar II", "lemmaOperator": "wrong operator"})


def test_parse_lines():
    assert parse_lines(["1", "2", "3"]) == [1, 2, 3]


def test_parse_lines_invalid():
    with pytest.raises(
        DataError,
        match=re.escape("lines must be a list of integers, got ['1', '?'] instead"),
    ):
        parse_lines(["1", "?"])


def test_parse_transliteration(sign_repository):
    factory = TransliterationQueryFactory(sign_repository)
    parse = parse_transliteration(factory)
    assert parse(PARAMS) == {
        **PARAMS,
        "transliteration": [
            factory.create(line).regexp
            for line in PARAMS["transliteration"].splitlines()
        ],
    }


def test_pipeline(sign_repository):
    factory = TransliterationQueryFactory(sign_repository)
    process = flow(
        parse_integer_field("limit"),
        parse_pages,
        parse_lemmas,
        parse_transliteration(factory),
    )
    assert process(PARAMS) == {
        "bibId": "author123",
        "lemmaOperator": LemmaQueryType.OR,
        "lemmas": ["first I", "second II"],
        "limit": 42,
        "pages": "3",
        "transliteration": [
            factory.create(line).regexp
            for line in PARAMS["transliteration"].splitlines()
        ],
    }


@pytest.mark.parametrize(
    "genre_input,expected_genre",
    [
        (["CANONICAL"], ["CANONICAL"]),
        (["CANONICAL", "Technical"], ["CANONICAL", "Technical"]),
        (["Non defined"], ["Non defined"]),
        (["CANONICAL", "Non defined"], ["CANONICAL", "Non defined"]),
        ("CANONICAL:Technical", ["CANONICAL", "Technical"]),
        ("CANONICAL", ["CANONICAL"]),
        ([], None),
        ("", None),
    ],
)
def test_parse_genre(genre_input, expected_genre):
    if expected_genre is None:
        assert parse_genre({"genre": genre_input}) == {"genre": genre_input}
    else:
        assert parse_genre({"genre": genre_input}) == {"genre": expected_genre}


def test_parse_genre_missing():
    assert parse_genre({}) == {}
