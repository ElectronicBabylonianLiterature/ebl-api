import logging
from typing import cast

import pytest
from pymongo import UpdateOne
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import BulkWriteError

from ebl.tests.transliteration.legacy_named_sign import (
    LEGACY_BREAK,
    LEGACY_PART,
    LEGACY_TAIL,
    MODULE,
    legacy_name,
    stored_document,
    value_at,
)
from ebl.transliteration import migrate_name_breaks
from ebl.transliteration.migrate_name_breaks import (
    MigrationWriteFailed,
    migrate_collection,
)
from ebl.transliteration.migrate_name_breaks_validation import NonAlternatingName

ONE_PART_NAME = {"nameParts": [LEGACY_PART]}
TOO_LARGE = "Resulting document after update is larger than 16777216"


@pytest.fixture
def fragments(database: Database) -> Collection:
    database.fragments.delete_many({})
    return database.fragments


def test_a_document_with_only_one_part_names_is_left_alone(
    fragments: Collection,
) -> None:
    fragments.insert_one({"_id": "K.1", "parts": [ONE_PART_NAME, ONE_PART_NAME]})

    assert migrate_collection(fragments, dry_run=True) == 0
    assert migrate_collection(fragments, dry_run=False) == 0
    assert stored_document(fragments, "K.1")["parts"] == [ONE_PART_NAME] * 2


def test_only_names_with_breaks_are_written(fragments: Collection) -> None:
    fragments.insert_one({"_id": "K.1", "parts": [ONE_PART_NAME, legacy_name()]})

    assert migrate_collection(fragments, dry_run=False) == 1

    stored = stored_document(fragments, "K.1")
    assert value_at(stored, "parts.0") == ONE_PART_NAME
    assert value_at(stored, "parts.1") == {
        "nameParts": [LEGACY_PART, LEGACY_TAIL],
        "nameBreaks": [LEGACY_BREAK],
    }


def test_a_one_part_name_that_is_a_break_is_still_refused(
    fragments: Collection,
) -> None:
    fragments.insert_one({"_id": "K.1", "parts": [{"nameParts": [LEGACY_BREAK]}]})

    with pytest.raises(NonAlternatingName, match="'K.1'"):
        migrate_collection(fragments, dry_run=True)


class FailingFragments:
    name = "fragments"

    def bulk_write(self, requests: list[UpdateOne]) -> None:
        raise BulkWriteError(
            {
                "writeErrors": [
                    {
                        "index": 0,
                        "code": 17419,
                        "errmsg": TOO_LARGE,
                        "op": {"q": {"_id": "K.1", "huge": "x" * 1000}},
                    }
                ],
                "nMatched": 0,
            }
        )


def test_a_write_error_is_reported_briefly(caplog: pytest.LogCaptureFixture) -> None:
    update = UpdateOne({"_id": "K.1"}, {"$set": {"a": 1}})

    with caplog.at_level(logging.ERROR, logger=MODULE):
        with pytest.raises(MigrationWriteFailed) as error:
            migrate_name_breaks._apply_updates(
                cast(Collection, FailingFragments()), iter([update])
            )

    assert str(error.value) == (
        f"fragments document 'K.1' could not be written: {TOO_LARGE} (code 17419)"
    )
    assert error.value.__cause__ is None
    assert "aborted; 0 documents written before the abort" in caplog.text
