import pytest
from marshmallow import ValidationError
from pymongo.database import Database

from ebl.signs.infrastructure.mongo_mes_zl_kap2_repository import (
    COLLECTION,
    MongoMesZlKap2Repository,
)
from ebl.tests.signs.mes_zl_kap2_data import FIRST, PRIMED, SECOND, SHARED


@pytest.mark.usefixtures("mes_zl_kap2_entries")
def test_keeps_the_order_of_the_numbers(
    mes_zl_kap2_repository: MongoMesZlKap2Repository,
) -> None:
    assert mes_zl_kap2_repository.find_by_numbers(["580", "579"]) == [SECOND, FIRST]


@pytest.mark.usefixtures("mes_zl_kap2_entries")
@pytest.mark.parametrize("number", ["214'", "214’", "214ʹ", " 214′ "])
def test_normalizes_primes(
    mes_zl_kap2_repository: MongoMesZlKap2Repository, number: str
) -> None:
    assert mes_zl_kap2_repository.find_by_numbers([number]) == [PRIMED]


@pytest.mark.usefixtures("mes_zl_kap2_entries")
def test_resolves_aliases_and_returns_each_entry_once(
    mes_zl_kap2_repository: MongoMesZlKap2Repository,
) -> None:
    assert mes_zl_kap2_repository.find_by_numbers(
        ["115a", "579", "115", "115b", "579"]
    ) == [SHARED, FIRST]


@pytest.mark.usefixtures("mes_zl_kap2_entries")
def test_skips_numbers_without_entry(
    mes_zl_kap2_repository: MongoMesZlKap2Repository,
) -> None:
    assert mes_zl_kap2_repository.find_by_numbers(["999", "579"]) == [FIRST]


@pytest.mark.parametrize("numbers", [[], ["", "  "]])
def test_without_numbers(
    mes_zl_kap2_repository: MongoMesZlKap2Repository, numbers: list[str]
) -> None:
    assert mes_zl_kap2_repository.find_by_numbers(numbers) == []


def test_rejects_malformed_documents(
    mes_zl_kap2_repository: MongoMesZlKap2Repository, database: Database
) -> None:
    database[COLLECTION].insert_one({"_id": "1", "text": "1\tNo aliases."})
    with pytest.raises(ValidationError):
        mes_zl_kap2_repository.find_by_numbers(["1"])
