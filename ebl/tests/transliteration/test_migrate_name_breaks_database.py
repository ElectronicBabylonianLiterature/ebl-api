import logging

import pytest

from ebl.tests.transliteration.legacy_named_sign import (
    LEGACY_BREAK,
    LEGACY_PART,
    LEGACY_TAIL,
    legacy_fragment,
    named_sign,
)
from ebl.transliteration import migrate_name_breaks
from ebl.transliteration.migrate_name_breaks import (
    NonAlternatingName,
    migrate,
    migrate_collection,
)

MODULE = "ebl.transliteration.migrate_name_breaks"


@pytest.fixture
def fragments(database):
    database.fragments.delete_many({})
    database.fragments.insert_one({"_id": "K.1", **legacy_fragment()})
    return database.fragments


def _stored(fragments, document_id="K.1"):
    return named_sign(fragments.find_one({"_id": document_id}))


def test_a_refused_name_names_the_collection_and_the_document(fragments) -> None:
    fragments.update_one(
        {"_id": "K.1"},
        {"$set": {"text.lines.0.content.0.parts.0.nameParts": [LEGACY_PART] * 2}},
    )

    with pytest.raises(NonAlternatingName, match="fragments document 'K.1'"):
        migrate_collection(fragments, dry_run=True)


def test_a_dry_run_reports_without_writing(fragments) -> None:
    assert migrate_collection(fragments, dry_run=True) == 1

    assert "nameBreaks" not in _stored(fragments)


def test_a_dry_run_never_writes(fragments, monkeypatch) -> None:
    def refuse_to_write(*args, **kwargs):
        raise AssertionError("a dry run must not write")

    monkeypatch.setattr(type(fragments), "bulk_write", refuse_to_write)

    assert migrate_collection(fragments, dry_run=True) == 1


def test_applying_writes_the_separated_arrays(fragments) -> None:
    assert migrate_collection(fragments, dry_run=False) == 1

    assert _stored(fragments)["nameParts"] == [LEGACY_PART, LEGACY_TAIL]
    assert _stored(fragments)["nameBreaks"] == [LEGACY_BREAK]


def test_an_edit_to_another_field_survives_the_migration(fragments) -> None:
    fragments.update_one({"_id": "K.1"}, {"$set": {"notes": "original"}})
    pending = list(migrate_name_breaks._pending_updates(fragments))
    fragments.update_one({"_id": "K.1"}, {"$set": {"notes": "edited by a user"}})

    assert migrate_name_breaks._apply_updates(fragments, iter(pending)) == 1

    stored = fragments.find_one({"_id": "K.1"})
    assert stored["notes"] == "edited by a user"
    assert named_sign(stored)["nameBreaks"] == [LEGACY_BREAK]


def test_a_document_edited_during_the_scan_is_not_overwritten(fragments, caplog):
    pending = list(migrate_name_breaks._pending_updates(fragments))
    fragments.update_one(
        {"_id": "K.1"},
        {"$set": {"text.lines.0.content.0.parts.0.name": "edited by a user"}},
    )

    with caplog.at_level(logging.WARNING):
        assert migrate_name_breaks._apply_updates(fragments, iter(pending)) == 0

    assert _stored(fragments)["name"] == "edited by a user"
    assert "nameBreaks" not in _stored(fragments)
    assert "run the migration again" in caplog.text


def test_migrating_again_changes_nothing(fragments) -> None:
    migrate_collection(fragments, dry_run=False)

    assert migrate_collection(fragments, dry_run=False) == 0


def test_migrate_reports_every_present_collection(database, fragments) -> None:
    counts = migrate(database, dry_run=True)

    assert counts["fragments"] == 1
    assert set(counts) <= {"fragments", "texts", "chapters"}


def test_a_missing_collection_is_reported(database, caplog) -> None:
    with caplog.at_level(logging.WARNING):
        assert migrate(database, dry_run=True) == {}

    assert "no such collection" in caplog.text


def test_batches_larger_than_the_batch_size_are_written(fragments, monkeypatch):
    fragments.delete_many({})
    fragments.insert_many(
        [{"_id": f"K.{index}", **legacy_fragment()} for index in range(3)]
    )
    monkeypatch.setattr(MODULE + ".BATCH_SIZE", 2)

    assert migrate_collection(fragments, dry_run=False) == 3

    for index in range(3):
        assert _stored(fragments, f"K.{index}")["nameBreaks"] == [LEGACY_BREAK]
