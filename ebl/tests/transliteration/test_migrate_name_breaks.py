import runpy
import sys
from typing import Any, Dict

import pymongo
import pytest

from ebl.tests.transliteration.legacy_named_sign import (
    LEGACY_BREAK,
    LEGACY_PART,
    LEGACY_TAIL,
    legacy_fragment,
    named_sign,
)
from ebl.transliteration.migrate_name_breaks import (
    NonAlternatingName,
    get_database,
    main,
    migrate_document,
    separate_name_parts,
)

MODULE = "ebl.transliteration.migrate_name_breaks"


def test_separating_takes_alternating_positions() -> None:
    assert separate_name_parts([LEGACY_PART, LEGACY_BREAK, LEGACY_TAIL]) == (
        [LEGACY_PART, LEGACY_TAIL],
        [LEGACY_BREAK],
    )


def test_separating_an_unbroken_name_yields_no_breaks() -> None:
    assert separate_name_parts([LEGACY_PART]) == ([LEGACY_PART], [])


def test_two_adjacent_parts_are_refused_rather_than_mis_split() -> None:
    with pytest.raises(NonAlternatingName, match="position 1"):
        separate_name_parts([LEGACY_PART, LEGACY_TAIL])


def test_a_break_in_a_part_position_is_refused() -> None:
    with pytest.raises(NonAlternatingName, match="position 0"):
        separate_name_parts([LEGACY_BREAK, LEGACY_PART])


def test_a_name_part_that_is_not_a_mapping_is_refused() -> None:
    with pytest.raises(NonAlternatingName, match="position 0"):
        separate_name_parts(["ku"])


@pytest.mark.parametrize("name_parts", [None, "ku", 7, {"type": "ValueToken"}])
def test_name_parts_that_is_not_an_array_is_refused(name_parts) -> None:
    with pytest.raises(NonAlternatingName, match="to be an array"):
        separate_name_parts(name_parts)


def test_a_nested_legacy_name_is_separated() -> None:
    document = legacy_fragment()

    assert migrate_document(document) is True

    assert named_sign(document)["nameParts"] == [LEGACY_PART, LEGACY_TAIL]
    assert named_sign(document)["nameBreaks"] == [LEGACY_BREAK]


def test_an_already_migrated_document_is_left_alone() -> None:
    document = legacy_fragment()
    migrate_document(document)

    assert migrate_document(document) is False


def test_a_document_without_names_is_left_alone() -> None:
    assert migrate_document({"text": {"lines": []}}) is False
    assert migrate_document([{"a": 1}, "b", 3]) is False


def test_get_database_uses_the_environment(monkeypatch) -> None:
    monkeypatch.setenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
    monkeypatch.setenv("MONGODB_DB", "ebl_migrate_name_breaks_probe")

    database = get_database()

    assert database.name == "ebl_migrate_name_breaks_probe"
    database.client.close()


def test_get_database_requires_the_database_name(monkeypatch) -> None:
    monkeypatch.setenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
    monkeypatch.delenv("MONGODB_DB", raising=False)

    with pytest.raises(KeyError, match="MONGODB_DB"):
        get_database()


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
        name = "ebl_migrate_probe"

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
