from ebl.signs.infrastructure.memoizing_sign_repository import MemoizingSignRepository


def test_find_memoization(sign_repository, signs, when):
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

    assert first == sign
    assert first is second


def test_search_by_lists_name_memoization(sign_repository, signs):
    sign = signs[0]
    name = sign.lists[0].name
    number = sign.lists[0].number

    memoizing_sign_repository = MemoizingSignRepository(sign_repository)
    memoizing_sign_repository.create(sign)

    first = memoizing_sign_repository.search_by_lists_name(name, number)
    second = memoizing_sign_repository.search_by_lists_name(name, number)

    assert [sign] == first
    assert first is second


def test_search_include_homophones(sign_repository, signs):
    sign = signs[0]
    value = sign.values[0].value

    memoizing_sign_repository = MemoizingSignRepository(sign_repository)
    memoizing_sign_repository.create(sign)

    first = memoizing_sign_repository.search_include_homophones(value)
    second = memoizing_sign_repository.search_include_homophones(value)

    assert [sign] == first
    assert first is second


def test_search_composite_signs(sign_repository, signs):
    sign = signs[0]
    value = sign.values[0].value
    sub_index = sign.values[0].sub_index

    memoizing_sign_repository = MemoizingSignRepository(sign_repository)
    memoizing_sign_repository.create(sign)

    first = memoizing_sign_repository.search_composite_signs(value, sub_index)
    second = memoizing_sign_repository.search_composite_signs(value, sub_index)
    assert [sign] == first
    assert first is second


def test_search_by_id(sign_repository, signs):
    sign = signs[0]
    name = sign.name

    memoizing_sign_repository = MemoizingSignRepository(sign_repository)
    memoizing_sign_repository.create(sign)

    first = memoizing_sign_repository.search_by_id(name)
    second = memoizing_sign_repository.search_by_id(name)
    assert [sign] == first
    assert first is second


def test_search_all(sign_repository, signs):
    sign = signs[0]
    value = sign.values[0].value
    sub_index = sign.values[0].sub_index

    memoizing_sign_repository = MemoizingSignRepository(sign_repository)
    memoizing_sign_repository.create(sign)

    first = memoizing_sign_repository.search_all(value, sub_index)
    second = memoizing_sign_repository.search_all(value, sub_index)
    assert [sign] == first
    assert first is second


def test_search_by_lemma(sign_repository, signs):
    sign = signs[0]
    word_id = sign.logograms[0].word_id[0]

    memoizing_sign_repository = MemoizingSignRepository(sign_repository)
    memoizing_sign_repository.create(sign)

    first = memoizing_sign_repository.search_by_lemma(word_id)
    second = memoizing_sign_repository.search_by_lemma(word_id)

    assert [sign] == first
    assert first is second
