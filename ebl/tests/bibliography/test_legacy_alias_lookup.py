from typing import Optional

import pytest
from pymongo.cursor import Cursor
from pymongo.database import Database

from ebl.bibliography.application.bibliography_identity import (
    ensure_lookup_values_available,
)
from ebl.bibliography.application.bibliography_repository import (
    BibliographyRepository,
    LookupValueInUseError,
)
from ebl.bibliography.infrastructure.legacy_alias_lookup import (
    LEGACY_ALIAS_FILTER,
    LEGACY_ALIAS_PROJECTION,
    MongoLegacyAliasLookup,
    legacy_normalized_aliases,
)
from ebl.mongo_collection import MongoCollection

FindCall = tuple[dict, tuple[object, ...]]
LEGACY_SCAN: FindCall = (LEGACY_ALIAS_FILTER, (LEGACY_ALIAS_PROJECTION,))


def seed(database: Database, id_: str, *aliases: object) -> None:
    database["bibliography"].insert_one(
        {"_id": id_, "type": "book", "aliases": list(aliases)}
    )


@pytest.fixture
def find_calls(monkeypatch: pytest.MonkeyPatch) -> list[FindCall]:
    calls: list[FindCall] = []
    find_many = MongoCollection.find_many

    def recording_find_many(
        self: MongoCollection, query: dict, *args: object, **kwargs: object
    ) -> Cursor:
        calls.append((query, args))
        return find_many(self, query, *args, **kwargs)

    monkeypatch.setattr(MongoCollection, "find_many", recording_find_many)
    return calls


def test_owners_maps_each_value_to_its_legacy_alias_owner(database: Database) -> None:
    seed(database, "A", {"value": "Legacy Alias"})
    seed(database, "B", {"value": "Other Alias", "normalizedValue": None})
    seed(database, "C", {"value": "Legacy Alias", "normalizedValue": "legacy-alias"})

    owners = MongoLegacyAliasLookup(database).owners(
        ["legacy alias", "other-alias", "missing"]
    )

    assert owners == {"legacy alias": ["A"], "other-alias": ["B"]}


def test_owners_lists_every_owner_of_an_ambiguous_legacy_alias(
    database: Database,
) -> None:
    seed(database, "A", {"value": "Shared Legacy"})
    seed(database, "B", {"value": "shared-legacy", "normalizedValue": ""})

    owners = MongoLegacyAliasLookup(database).owners(["Shared Legacy"])

    assert sorted(owners["Shared Legacy"]) == ["A", "B"]


def test_owners_scans_once_with_a_projection(
    database: Database, find_calls: list[FindCall]
) -> None:
    seed(database, "A", {"value": "First"}, {"value": "Second"})

    owners = MongoLegacyAliasLookup(database).owners(["first", "second", "third"])

    assert owners == {"first": ["A"], "second": ["A"]}
    assert find_calls == [LEGACY_SCAN]


def test_owners_skips_the_scan_when_no_value_can_match(
    database: Database, find_calls: list[FindCall]
) -> None:
    seed(database, "A", {"value": "!!!"})

    assert MongoLegacyAliasLookup(database).owners(["!!!", ""]) == {}
    assert MongoLegacyAliasLookup(database).owners([]) == {}
    assert find_calls == []


def test_owners_ignores_normalized_and_non_string_aliases(database: Database) -> None:
    seed(
        database,
        "A",
        {"value": 7},
        {"value": "Legacy Alias", "normalizedValue": "legacy-alias"},
    )

    assert MongoLegacyAliasLookup(database).owners(["legacy alias"]) == {}


def test_legacy_normalized_aliases_keeps_only_legacy_shaped_aliases() -> None:
    entry = {
        "aliases": [
            "Plain String",
            {"value": 7},
            {"value": "Normalized", "normalizedValue": "normalized"},
            {"value": "Legacy Alias", "normalizedValue": None},
            {"value": "Other Legacy"},
        ]
    }

    assert legacy_normalized_aliases(entry) == {"legacy-alias", "other-legacy"}


def test_the_sole_legacy_owner_may_keep_its_value(
    bibliography_repository: BibliographyRepository, database: Database
) -> None:
    seed(database, "A", {"value": "Legacy Alias"})

    ensure_lookup_values_available(bibliography_repository, ["legacy alias"], "A")


@pytest.mark.parametrize("allowed_id", [None, "A", "B"])
def test_another_legacy_owner_blocks_the_value(
    bibliography_repository: BibliographyRepository,
    database: Database,
    allowed_id: Optional[str],
) -> None:
    seed(database, "A", {"value": "Shared Legacy"})
    seed(database, "B", {"value": "Shared-Legacy"})

    with pytest.raises(LookupValueInUseError):
        ensure_lookup_values_available(
            bibliography_repository, ["shared legacy"], allowed_id
        )


def test_availability_scans_legacy_aliases_once_per_write(
    bibliography_repository: BibliographyRepository,
    database: Database,
    find_calls: list[FindCall],
) -> None:
    seed(database, "A", {"value": "Legacy Alias"})

    ensure_lookup_values_available(
        bibliography_repository, ["first", "second", "third"], "B"
    )

    assert find_calls.count(LEGACY_SCAN) == 1
