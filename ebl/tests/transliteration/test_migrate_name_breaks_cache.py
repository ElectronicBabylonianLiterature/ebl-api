import logging

import pytest
from pymongo.collection import Collection
from pymongo.database import Database

from ebl.tests.transliteration.legacy_named_sign import (
    LEGACY_PART,
    MODULE,
    legacy_fragment,
    named_sign,
)
from ebl.transliteration.migrate_name_breaks import clear_cache, main, migrate
from ebl.transliteration.migrate_name_breaks_validation import NonAlternatingName


def test_migrate_leaves_the_chapter_display_cache_alone(database: Database) -> None:
    database.cache.insert_one({"cache_key": "L I.1 1", **legacy_fragment()})

    assert "cache" not in migrate(database, dry_run=False)

    stored = named_sign(database.cache.find_one({"cache_key": "L I.1 1"}))
    assert "nameBreaks" not in stored


@pytest.fixture
def cache(database: Database) -> Collection:
    database.cache.delete_many({})
    database.cache.insert_many(
        [{"cache_key": f"L I.1 {line}", **legacy_fragment()} for line in (1, 2)]
    )
    return database.cache


def test_a_dry_run_counts_the_cache_without_clearing_it(
    database: Database, cache: Collection
) -> None:
    assert clear_cache(database, dry_run=True) == 2

    assert cache.count_documents({}) == 2


def test_applying_clears_the_cache(
    database: Database, cache: Collection, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO):
        assert clear_cache(database, dry_run=False) == 2

    assert cache.count_documents({}) == 0
    assert "cache: 2 entries cleared" in caplog.text


def test_an_aborted_run_has_already_cleared_the_cache(
    database: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    database.fragments.insert_one({"_id": "K.1", "nameParts": [LEGACY_PART] * 2})
    database.cache.insert_one({"cache_key": "L I.1 1", **legacy_fragment()})
    monkeypatch.setattr(MODULE + ".get_database", lambda: database)

    with pytest.raises(NonAlternatingName, match="fragments document 'K.1'"):
        main(["--apply"])

    assert database.cache.count_documents({}) == 0
