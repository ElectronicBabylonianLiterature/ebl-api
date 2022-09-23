import pytest

from ebl.errors import DataError
from ebl.transliteration.application.transliteration_query_factory import (
    TransliterationQueryFactory,
)
from ebl.transliteration.domain.transliteration_query import TransliterationQuery


def test_create_empty():
    assert TransliterationQueryFactory.create_empty().is_empty() is True


def test_create_query(sign_repository, signs):
    for sign in signs:
        sign_repository.create(sign)

    factory = TransliterationQueryFactory(sign_repository)
    atf = "šu\ngid₂\nBU"

    query = TransliterationQuery(string="ŠU\nBU", sign_repository=sign_repository)
    factory_query = factory.create(atf)
    assert factory_query.regexp == query.regexp


def test_create_query_invalid(sign_repository):
    factory = TransliterationQueryFactory(sign_repository)
    with pytest.raises(DataError):
        factory.create("$ (invalid query)")
