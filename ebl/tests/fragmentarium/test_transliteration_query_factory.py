from ebl.fragmentarium.application.transliteration_query_factory import (
    TransliterationQueryFactory,
)
from ebl.fragmentarium.domain.transliteration_query import TransliterationQuery


def test_create_query(atf_converter, sign_repository, signs):
    for sign in signs:
        sign_repository.create(sign)

    factory = TransliterationQueryFactory(sign_repository)
    atf = "šu\ngid₂"

    assert factory.create(atf) == TransliterationQuery([["ŠU"], ["BU"]])
