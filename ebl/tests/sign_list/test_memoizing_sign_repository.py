from ebl.sign_list.sign_repository import MemoizingSignRepository


def test_search_memoization(database, signs):
    sign = signs[0]
    value = sign['values'][0]['value']
    sub_index = sign['values'][0]['subIndex']

    memoizing_sign_repository = MemoizingSignRepository(database)
    memoizing_sign_repository.create(sign)

    first = memoizing_sign_repository.search(value, sub_index)
    second = memoizing_sign_repository.search(value, sub_index)

    assert first is second


def test_search_many_memoization(database, signs):
    sign = signs[0]
    value = sign['values'][0]['value']
    sub_index = sign['values'][0]['subIndex']

    memoizing_sign_repository = MemoizingSignRepository(database)
    memoizing_sign_repository.create(sign)

    first = memoizing_sign_repository.search_many([(value, sub_index)])
    second = memoizing_sign_repository.search_many([(value, sub_index)])

    assert first is second
