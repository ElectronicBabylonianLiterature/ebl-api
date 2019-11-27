from ebl.transliteration.infrastructure.menoizing_sign_repository import (
    MemoizingSignRepository,
)


def test_find_memoization(sign_repository, signs):
    sign = signs[0]

    memoizing_sign_repository = MemoizingSignRepository(sign_repository)
    memoizing_sign_repository.create(sign)

    first = memoizing_sign_repository.find(sign.name)
    second = memoizing_sign_repository.find(sign.name)

    assert first is second


def test_search_memoization(sign_repository, signs):
    sign = signs[0]
    value = sign.values[0].value
    sub_index = sign.values[0].sub_index

    memoizing_sign_repository = MemoizingSignRepository(sign_repository)
    memoizing_sign_repository.create(sign)

    first = memoizing_sign_repository.search(value, sub_index)
    second = memoizing_sign_repository.search(value, sub_index)

    assert first is second


def test_search_many_memoization(sign_repository, signs):
    sign = signs[0]
    value = sign.values[0]

    memoizing_sign_repository = MemoizingSignRepository(sign_repository)
    memoizing_sign_repository.create(sign)

    first = memoizing_sign_repository.search_many([value])
    second = memoizing_sign_repository.search_many([value])

    assert first is second
