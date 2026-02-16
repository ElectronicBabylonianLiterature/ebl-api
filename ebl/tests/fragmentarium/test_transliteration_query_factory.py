import pytest

from ebl.errors import DataError
from ebl.transliteration.application.transliteration_query_factory import (
    TransliterationQueryFactory,
)
from ebl.transliteration.domain.transliteration_query import TransliterationQuery
from ebl.transliteration.application.signs_visitor import SignsVisitor


def test_create_empty():
    assert TransliterationQueryFactory.create_empty().is_empty() is True


def test_create_query(sign_repository, signs):
    for sign in signs:
        sign_repository.create(sign)
    visitor = SignsVisitor(sign_repository)
    factory = TransliterationQueryFactory(sign_repository)
    atf = "šu\ngid₂"

    query = TransliterationQuery(string="ŠU\nBU", visitor=visitor)
    factory_query = factory.create(atf)
    assert factory_query.regexp == query.regexp


def test_create_query_invalid(sign_repository):
    factory = TransliterationQueryFactory(sign_repository)
    with pytest.raises(DataError):
        factory.create("$ (invalid query)")
