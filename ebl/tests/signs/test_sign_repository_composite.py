from ebl.signs.infrastructure.mongo_sign_repository import MongoSignRepository


def test_search_composite_signs_matches_the_reading(database, signs) -> None:
    repository = MongoSignRepository(database)
    for sign in signs:
        repository.create(sign)
    value = signs[0].values[0]

    result = repository.search_composite_signs(value.value, value.sub_index)

    assert [sign.name for sign in result] == [signs[0].name]


def test_search_composite_signs_without_a_match(database, signs) -> None:
    repository = MongoSignRepository(database)
    for sign in signs:
        repository.create(sign)

    assert repository.search_composite_signs("not a reading", 1) == []
