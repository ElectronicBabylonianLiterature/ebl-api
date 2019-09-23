from ebl.atf.atf import Atf
from ebl.transliteration_search.transliteration_query import \
    TransliterationQuery
from ebl.transliteration_search.transliteration_query_factory import \
    TransliterationQueryFactory


def test_create_query(transliteration_search, sign_repository, signs):
    for sign in signs:
        sign_repository.create(sign)

    factory = TransliterationQueryFactory(transliteration_search)
    atf = Atf('1. šu\n2. gid₂')

    assert factory.create(atf) == TransliterationQuery([['ŠU'], ['BU']])
