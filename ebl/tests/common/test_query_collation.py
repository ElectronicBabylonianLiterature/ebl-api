import re
from typing import cast

import pytest

from ebl.common.query.query_collation import (
    WILDCARD_AND_COLLATION_MATCHERS,
    CollatedFieldQuery,
    DataType,
    Fields,
    make_query_params_from_string,
)

COLLATED_H = r"[hḫḥHḪḤʕʾʿ]"
SPELLINGS = ["ḫattusa", "Ḫattusa", "Ḥattusa", "Hattusa", "ḥattuša"]


@pytest.mark.parametrize("query", SPELLINGS)
def test_h_collates_regardless_of_case(query: str) -> None:
    assert CollatedFieldQuery(query, "_id", "realia").value.startswith(COLLATED_H)


@pytest.mark.parametrize("query", SPELLINGS)
@pytest.mark.parametrize("stored", SPELLINGS)
def test_every_spelling_matches_every_other(query: str, stored: str) -> None:
    assert re.search(CollatedFieldQuery(query, "_id", "realia").value, stored)


@pytest.mark.parametrize("query", SPELLINGS)
def test_collated_h_does_not_match_another_initial(query: str) -> None:
    assert (
        re.search(CollatedFieldQuery(query, "_id", "realia").value, "Battusa") is None
    )


def test_uppercase_h_collates_in_dictionary_word_field() -> None:
    assert CollatedFieldQuery("Ḫ", "word", "dictionary").value == COLLATED_H


def test_uncollated_characters_are_escaped_literally() -> None:
    assert CollatedFieldQuery("B.q", "_id", "realia").value == re.escape("B.q")


def test_colophon_names_are_collated() -> None:
    assert CollatedFieldQuery("Ḫattusa", "names", "colophons").value.startswith(
        COLLATED_H
    )


def test_unknown_data_type_is_rejected() -> None:
    with pytest.raises(ValueError):
        Fields.findByDataType(cast(DataType, "unknown"))


def test_query_params_are_built_from_a_query_string() -> None:
    params = list(make_query_params_from_string("word=Ḫattusa", "dictionary"))

    assert [param.field for param in params] == ["word"]
    assert params[0].value.startswith(COLLATED_H)


def test_empty_query_string_yields_no_params() -> None:
    assert list(make_query_params_from_string("")) == []


@pytest.mark.parametrize("name", list(WILDCARD_AND_COLLATION_MATCHERS))
@pytest.mark.parametrize("key", ["wildcard", "regex"])
def test_no_collation_class_contains_a_literal_pipe(name: str, key: str) -> None:
    pattern = WILDCARD_AND_COLLATION_MATCHERS[name][key]

    assert "|" not in pattern


def test_literal_pipe_is_escaped_not_collated() -> None:
    assert CollatedFieldQuery("|", "_id", "realia").value == re.escape("|")


def test_pipe_query_does_not_match_a_collated_letter() -> None:
    value = CollatedFieldQuery("|", "_id", "realia").value

    assert re.search(value, "šamaš") is None


def test_collated_h_does_not_match_a_literal_pipe() -> None:
    value = CollatedFieldQuery("hattusa", "_id", "realia").value

    assert re.search(value, "|attusa") is None


COLLATION_NAMES = [
    name for name in WILDCARD_AND_COLLATION_MATCHERS if name.startswith("collation")
]
CASE_PAIRS = [
    ("Samas", "šamaš"),
    ("Šamaš", "samas"),
    ("Tab", "ṭāb"),
    ("Ṭāb", "tab"),
    ("Lowe", "łowe"),
    ("ANU", "anu"),
    ("Ekur", "ékur"),
    ("Ninurta", "ninurta"),
]


@pytest.mark.parametrize("name", COLLATION_NAMES)
@pytest.mark.parametrize("key", ["wildcard", "regex"])
def test_every_collation_class_contains_its_uppercase(name: str, key: str) -> None:
    characters = WILDCARD_AND_COLLATION_MATCHERS[name][key][1:-1]

    missing = [
        character
        for character in characters
        if len(character.upper()) == 1 and character.upper() not in characters
    ]

    assert missing == []


@pytest.mark.parametrize("query,stored", CASE_PAIRS)
def test_uppercase_queries_collate_in_every_group(query: str, stored: str) -> None:
    assert re.search(CollatedFieldQuery(query, "_id", "realia").value, stored)


def test_letters_without_a_collation_group_stay_literal() -> None:
    assert CollatedFieldQuery("Bq", "_id", "realia").value == re.escape("Bq")
