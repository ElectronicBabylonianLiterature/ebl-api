import re
from typing import cast

import pytest

from ebl.common.query.query_collation import (
    CollatedFieldQuery,
    DataType,
    Fields,
    make_query_params_from_string,
)

COLLATED_H = r"[h|ḫ|ḥ|H|Ḫ|Ḥ|ʕ|ʾ|ʿ]"
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
