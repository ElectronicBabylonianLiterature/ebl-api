import logging
from collections.abc import Mapping
from typing import NoReturn

import pytest
from pymongo.collection import Collection
from pymongo.database import Database

from ebl.tests.transliteration.legacy_named_sign import (
    LEGACY_BREAK,
    LEGACY_PART,
    LEGACY_TAIL,
    MODULE,
    NAMED_SIGN_PATH,
    later_named_sign,
    legacy_fragment,
    legacy_fragment_with_a_later_name,
    legacy_name,
    named_sign,
    stored_document,
    value_at,
)
from ebl.transliteration import migrate_name_breaks
from ebl.transliteration.migrate_name_breaks import (
    migrate,
    migrate_collection,
)
from ebl.transliteration.migrate_name_breaks_validation import NonAlternatingName

SEPARATED = {"nameParts": [LEGACY_PART, LEGACY_TAIL], "nameBreaks": [LEGACY_BREAK]}


@pytest.fixture
def fragments(database: Database) -> Collection:
    database.fragments.delete_many({})
    database.fragments.insert_one({"_id": "K.1", **legacy_fragment()})
    return database.fragments


def _stored(fragments: Collection, document_id: str = "K.1") -> Mapping[str, object]:
    return named_sign(stored_document(fragments, document_id))


def _break_the_alternation(fragments: Collection, document_id: str) -> None:
    fragments.update_one(
        {"_id": document_id},
        {"$set": {f"{NAMED_SIGN_PATH}.nameParts": [LEGACY_PART] * 2}},
    )


def test_a_refused_name_names_the_collection_and_the_document(
    fragments: Collection,
) -> None:
    _break_the_alternation(fragments, "K.1")

    with pytest.raises(NonAlternatingName, match="fragments document 'K.1'"):
        migrate_collection(fragments, dry_run=True)


def test_a_dry_run_reports_without_writing(fragments: Collection) -> None:
    assert migrate_collection(fragments, dry_run=True) == 1

    assert "nameBreaks" not in _stored(fragments)


def test_a_dry_run_never_writes(
    fragments: Collection, monkeypatch: pytest.MonkeyPatch
) -> None:
    def refuse_to_write(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("a dry run must not write")

    monkeypatch.setattr(type(fragments), "bulk_write", refuse_to_write)

    assert migrate_collection(fragments, dry_run=True) == 1


def test_applying_writes_the_separated_arrays(fragments: Collection) -> None:
    assert migrate_collection(fragments, dry_run=False) == 1

    assert _stored(fragments) == SEPARATED


def test_names_beyond_the_first_item_of_every_list_are_written(
    fragments: Collection,
) -> None:
    fragments.insert_one({"_id": "K.2", **legacy_fragment_with_a_later_name()})

    assert migrate_collection(fragments, dry_run=False) == 2

    assert later_named_sign(stored_document(fragments, "K.2")) == SEPARATED


def test_a_name_in_a_nested_list_is_written(fragments: Collection) -> None:
    fragments.insert_one({"_id": "K.2", "rows": [[{"a": 1}, legacy_name()]]})

    migrate_collection(fragments, dry_run=False)

    assert value_at(stored_document(fragments, "K.2"), "rows.0.1") == SEPARATED


def test_a_document_too_large_to_write_back_whole_is_migrated(
    fragments: Collection,
) -> None:
    padding = "x" * 12_000_000
    fragments.update_one({"_id": "K.1"}, {"$set": {"text.padding": padding}})

    assert migrate_collection(fragments, dry_run=False) == 1

    stored = stored_document(fragments, "K.1")
    assert named_sign(stored) == SEPARATED
    assert value_at(stored, "text.padding") == padding


def test_an_edit_to_another_field_survives_the_migration(
    fragments: Collection,
) -> None:
    fragments.update_one({"_id": "K.1"}, {"$set": {"notes": "original"}})
    pending = list(migrate_name_breaks._pending_updates(fragments))
    fragments.update_one(
        {"_id": "K.1"},
        {
            "$set": {
                "notes": "edited by a user",
                f"{NAMED_SIGN_PATH}.name": "edited by a user",
            }
        },
    )

    assert migrate_name_breaks._apply_updates(fragments, iter(pending)) == 1

    stored = stored_document(fragments, "K.1")
    assert stored["notes"] == "edited by a user"
    assert named_sign(stored) == {**SEPARATED, "name": "edited by a user"}


def test_a_name_edited_during_the_scan_is_not_overwritten(
    fragments: Collection, caplog: pytest.LogCaptureFixture
) -> None:
    edited = {"nameParts": [LEGACY_TAIL], "nameBreaks": []}
    pending = list(migrate_name_breaks._pending_updates(fragments))
    fragments.update_one({"_id": "K.1"}, {"$set": {NAMED_SIGN_PATH: edited}})

    with caplog.at_level(logging.WARNING):
        assert migrate_name_breaks._apply_updates(fragments, iter(pending)) == 0

    assert _stored(fragments) == edited
    assert "changed or deleted while the migration was reading" in caplog.text


def test_a_document_deleted_during_the_scan_is_reported(
    fragments: Collection, caplog: pytest.LogCaptureFixture
) -> None:
    pending = list(migrate_name_breaks._pending_updates(fragments))
    fragments.delete_one({"_id": "K.1"})

    with caplog.at_level(logging.WARNING):
        assert migrate_name_breaks._apply_updates(fragments, iter(pending)) == 0

    assert "1 documents were changed or deleted" in caplog.text


def test_migrating_again_changes_nothing(fragments: Collection) -> None:
    migrate_collection(fragments, dry_run=False)

    assert migrate_collection(fragments, dry_run=False) == 0


def test_migrate_reports_every_present_collection(
    database: Database, fragments: Collection
) -> None:
    database.texts.insert_one({"_id": "T.1", **legacy_fragment()})

    assert migrate(database, dry_run=True) == {"fragments": 1, "texts": 1}


def test_an_abort_reports_what_was_already_written(
    fragments: Collection,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    fragments.insert_one({"_id": "K.2", **legacy_fragment()})
    _break_the_alternation(fragments, "K.2")
    monkeypatch.setattr(MODULE + ".BATCH_SIZE", 1)

    with caplog.at_level(logging.ERROR), pytest.raises(NonAlternatingName):
        migrate_collection(fragments, dry_run=False)

    assert "aborted; 1 documents written before the abort" in caplog.text
    assert _stored(fragments) == SEPARATED


def test_a_missing_collection_is_reported(
    database: Database, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.WARNING):
        assert migrate(database, dry_run=True) == {}

    assert "no such collection" in caplog.text


def test_batches_larger_than_the_batch_size_are_written(
    fragments: Collection, monkeypatch: pytest.MonkeyPatch
) -> None:
    fragments.delete_many({})
    fragments.insert_many(
        [{"_id": f"K.{index}", **legacy_fragment()} for index in range(3)]
    )
    monkeypatch.setattr(MODULE + ".BATCH_SIZE", 2)

    assert migrate_collection(fragments, dry_run=False) == 3

    for index in range(3):
        assert _stored(fragments, f"K.{index}")["nameBreaks"] == [LEGACY_BREAK]
