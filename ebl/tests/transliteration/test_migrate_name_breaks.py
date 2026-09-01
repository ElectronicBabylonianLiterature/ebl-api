import runpy
import sys

import pymongo
from typing import Any, Dict

import pytest

from ebl.transliteration.migrate_name_breaks import (
    get_database,
    main,
    migrate,
    migrate_collection,
    migrate_document,
    separate_name_parts,
)

MODULE = "ebl.transliteration.migrate_name_breaks"
LEGACY_PART = {"value": "k", "type": "ValueToken"}
LEGACY_BREAK = {"value": "]", "type": "BrokenAway", "side": "RIGHT"}
LEGACY_TAIL = {"value": "u", "type": "ValueToken"}


def _legacy_fragment() -> Dict[str, Any]:
    return {
        "text": {
            "lines": [
                {
                    "content": [
                        {
                            "parts": [
                                {"nameParts": [LEGACY_PART, LEGACY_BREAK, LEGACY_TAIL]}
                            ]
                        }
                    ]
                }
            ]
        }
    }


def test_separating_takes_alternating_positions() -> None:
    assert separate_name_parts([LEGACY_PART, LEGACY_BREAK, LEGACY_TAIL]) == (
        [LEGACY_PART, LEGACY_TAIL],
        [LEGACY_BREAK],
    )


def test_separating_an_unbroken_name_yields_no_breaks() -> None:
    assert separate_name_parts([LEGACY_PART]) == ([LEGACY_PART], [])


def test_a_nested_legacy_name_is_separated() -> None:
    document = _legacy_fragment()

    assert migrate_document(document) is True

    named_sign = document["text"]["lines"][0]["content"][0]["parts"][0]
    assert named_sign["nameParts"] == [LEGACY_PART, LEGACY_TAIL]
    assert named_sign["nameBreaks"] == [LEGACY_BREAK]


def test_an_already_migrated_document_is_left_alone() -> None:
    document = _legacy_fragment()
    migrate_document(document)

    assert migrate_document(document) is False


def test_a_document_without_names_is_left_alone() -> None:
    assert migrate_document({"text": {"lines": []}}) is False
    assert migrate_document([{"a": 1}, "b", 3]) is False


@pytest.fixture
def fragments(database):
    database.fragments.delete_many({})
    database.fragments.insert_one({"_id": "K.1", **_legacy_fragment()})
    return database.fragments


def test_a_dry_run_reports_without_writing(fragments) -> None:
    assert migrate_collection(fragments, dry_run=True) == 1

    stored = fragments.find_one({"_id": "K.1"})
    named_sign = stored["text"]["lines"][0]["content"][0]["parts"][0]
    assert "nameBreaks" not in named_sign


def test_applying_writes_the_separated_arrays(fragments) -> None:
    assert migrate_collection(fragments, dry_run=False) == 1

    stored = fragments.find_one({"_id": "K.1"})
    named_sign = stored["text"]["lines"][0]["content"][0]["parts"][0]
    assert named_sign["nameParts"] == [LEGACY_PART, LEGACY_TAIL]
    assert named_sign["nameBreaks"] == [LEGACY_BREAK]


def test_migrating_again_changes_nothing(fragments) -> None:
    migrate_collection(fragments, dry_run=False)

    assert migrate_collection(fragments, dry_run=False) == 0


def test_migrate_reports_every_present_collection(database, fragments) -> None:
    counts = migrate(database, dry_run=True)

    assert counts["fragments"] == 1
    assert set(counts) <= {"fragments", "texts", "chapters"}


def test_batches_larger_than_the_batch_size_are_written(fragments) -> None:
    from ebl.transliteration import migrate_name_breaks

    fragments.delete_many({})
    fragments.insert_many(
        [{"_id": f"K.{index}", **_legacy_fragment()} for index in range(3)]
    )
    monkey = migrate_name_breaks.BATCH_SIZE
    migrate_name_breaks.BATCH_SIZE = 2
    try:
        assert migrate_collection(fragments, dry_run=False) == 3
    finally:
        migrate_name_breaks.BATCH_SIZE = monkey

    for index in range(3):
        stored = fragments.find_one({"_id": f"K.{index}"})
        named_sign = stored["text"]["lines"][0]["content"][0]["parts"][0]
        assert named_sign["nameBreaks"] == [LEGACY_BREAK]


def test_get_database_uses_the_environment(monkeypatch, database) -> None:
    monkeypatch.setenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
    monkeypatch.setenv("MONGODB_DB", "ebl_migrate_name_breaks_probe")

    assert get_database().name == "ebl_migrate_name_breaks_probe"


@pytest.fixture
def recorded_migrate(monkeypatch):
    calls: Dict[str, Any] = {}

    def fake_migrate(database, dry_run):
        calls["dry_run"] = dry_run
        return {}

    monkeypatch.setattr(MODULE + ".migrate", fake_migrate)
    monkeypatch.setattr(MODULE + ".get_database", lambda: None)
    return calls


def test_main_defaults_to_a_dry_run(recorded_migrate) -> None:
    main([])

    assert recorded_migrate["dry_run"] is True


def test_main_applies_when_asked(recorded_migrate) -> None:
    main(["--apply"])

    assert recorded_migrate["dry_run"] is False


def test_running_the_module_as_a_script_invokes_main(monkeypatch) -> None:
    class _Database:
        def list_collection_names(self):
            return []

    class _Client:
        def __init__(self, uri):
            self.uri = uri

        def get_database(self, name):
            return _Database()

    monkeypatch.setattr(pymongo, "MongoClient", _Client)
    monkeypatch.setenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
    monkeypatch.setenv("MONGODB_DB", "ebl_migrate_probe")
    monkeypatch.setattr(sys, "argv", [MODULE])

    runpy.run_module(MODULE, run_name="__main__")
