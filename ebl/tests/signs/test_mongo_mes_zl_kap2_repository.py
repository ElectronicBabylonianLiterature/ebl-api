import pytest
from pymongo.database import Database

from ebl.signs.domain.mes_zl_kap2 import mes_zl_number_variants
from ebl.signs.infrastructure.mongo_mes_zl_kap2_repository import (
    COLLECTION,
    MongoMesZlKap2Repository,
)
from ebl.tests.signs.mes_zl_kap2_data import (
    DOCUMENTS,
    FIRST,
    PRIMED,
    SECOND,
    SHARED,
)


@pytest.fixture
def mes_zl_kap2_entries(database: Database) -> None:
    database[COLLECTION].insert_many([dict(document) for document in DOCUMENTS])


def test_number_variants() -> None:
    assert mes_zl_number_variants(" 214' ") == ("214'", "214′")
    assert mes_zl_number_variants("579") == ("579",)


@pytest.mark.usefixtures("mes_zl_kap2_entries")
def test_find_by_numbers_keeps_the_order_of_the_numbers(
    mes_zl_kap2_repository: MongoMesZlKap2Repository,
) -> None:
    assert mes_zl_kap2_repository.find_by_numbers(["580", "579"]) == [SECOND, FIRST]


@pytest.mark.usefixtures("mes_zl_kap2_entries")
def test_find_by_numbers_accepts_an_apostrophe_for_a_prime(
    mes_zl_kap2_repository: MongoMesZlKap2Repository,
) -> None:
    assert mes_zl_kap2_repository.find_by_numbers(["214'"]) == [PRIMED]


@pytest.mark.usefixtures("mes_zl_kap2_entries")
def test_find_by_numbers_resolves_aliases_once(
    mes_zl_kap2_repository: MongoMesZlKap2Repository,
) -> None:
    assert mes_zl_kap2_repository.find_by_numbers(["115a", "115"]) == [SHARED]


@pytest.mark.usefixtures("mes_zl_kap2_entries")
def test_find_by_numbers_skips_missing_numbers(
    mes_zl_kap2_repository: MongoMesZlKap2Repository,
) -> None:
    assert mes_zl_kap2_repository.find_by_numbers(["999", "579"]) == [FIRST]


def test_find_by_numbers_without_numbers(
    mes_zl_kap2_repository: MongoMesZlKap2Repository,
) -> None:
    assert mes_zl_kap2_repository.find_by_numbers([]) == []
