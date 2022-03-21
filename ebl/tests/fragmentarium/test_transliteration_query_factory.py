import pytest

from ebl.errors import DataError
from ebl.transliteration.application.transliteration_query_factory import (
    TransliterationQueryFactory,
)
from ebl.transliteration.domain.transliteration_query import TransliterationQuery


def test_create_query(sign_repository, signs):
    for sign in signs:
        sign_repository.create_many(sign)

    factory = TransliterationQueryFactory(sign_repository)
    atf = "šu\ngid₂"

    assert factory.create(atf) == TransliterationQuery([["ŠU"], ["BU"]])


def test_create_query_invalid(sign_repository):
    factory = TransliterationQueryFactory(sign_repository)
    with pytest.raises(DataError):
        factory.create("$ (invalid query)")
