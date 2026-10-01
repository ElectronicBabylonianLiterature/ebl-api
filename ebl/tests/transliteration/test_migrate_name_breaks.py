import logging
import runpy
import sys
from typing import Dict

import pymongo
import pytest

from ebl.tests.transliteration.legacy_named_sign import (
    LATER_NAMED_SIGN_PATH,
    LEGACY_BREAK,
    LEGACY_PART,
    LEGACY_TAIL,
    NAMED_SIGN_PATH,
    legacy_fragment,
    legacy_fragment_with_a_later_name,
    legacy_name,
)
from ebl.transliteration.migrate_name_breaks import (
    LegacyName,
    NonAlternatingName,
    find_legacy_names,
    get_database,
    main,
    separate_name_parts,
)

MODULE = "ebl.transliteration.migrate_name_breaks"


def _paths(document: object) -> list[str]:
    return [name.path for name in find_legacy_names(document)]


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


@pytest.mark.parametrize(
    "name_parts", [[LEGACY_PART, LEGACY_BREAK], []], ids=["trailing break", "empty"]
)
def test_a_name_that_does_not_end_with_a_part_is_refused(name_parts) -> None:
    with pytest.raises(NonAlternatingName, match="start and end with a ValueToken"):
        separate_name_parts(name_parts)


@pytest.mark.parametrize("name_parts", [None, "ku", 7, {"type": "ValueToken"}])
def test_name_parts_that_is_not_an_array_is_refused(name_parts) -> None:
    with pytest.raises(NonAlternatingName, match="to be an array"):
        separate_name_parts(name_parts)


def test_a_nested_legacy_name_is_found_with_its_path() -> None:
    assert list(find_legacy_names(legacy_fragment())) == [
        LegacyName(NAMED_SIGN_PATH, legacy_name()["nameParts"])
    ]


def test_a_legacy_name_after_the_first_item_of_every_list_is_found() -> None:
    assert _paths(legacy_fragment_with_a_later_name()) == [LATER_NAMED_SIGN_PATH]


def test_every_legacy_name_in_a_list_is_found() -> None:
    assert _paths([legacy_name(), {"a": 1}, legacy_name()]) == ["0", "2"]


def test_a_legacy_name_in_a_nested_list_is_found() -> None:
    assert _paths({"rows": [[{"a": 1}, legacy_name()]]}) == ["rows.0.1"]


def test_a_top_level_legacy_name_has_an_empty_path() -> None:
    assert _paths(legacy_name()) == [""]


def test_an_already_separated_name_is_left_alone() -> None:
    separated = {"nameParts": [LEGACY_PART], "nameBreaks": []}

    assert _paths({"text": {"lines": [separated]}}) == []


def test_a_document_without_names_is_left_alone() -> None:
    assert _paths({"text": {"lines": []}}) == []
    assert _paths([{"a": 1}, "b", 3]) == []


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
def recorded_dry_runs(monkeypatch) -> Dict[str, bool]:
    calls: Dict[str, bool] = {}

    def fake_migrate(database, dry_run):
        calls["migrate"] = dry_run
        return {}

    def fake_clear_cache(database, dry_run):
        calls["clear_cache"] = dry_run
        return 0

    monkeypatch.setattr(MODULE + ".migrate", fake_migrate)
    monkeypatch.setattr(MODULE + ".clear_cache", fake_clear_cache)
    monkeypatch.setattr(MODULE + ".get_database", lambda: None)
    return calls


def test_main_defaults_to_a_dry_run(recorded_dry_runs) -> None:
    main([])

    assert recorded_dry_runs == {"migrate": True, "clear_cache": True}


def test_main_applies_when_asked(recorded_dry_runs) -> None:
    main(["--apply"])

    assert recorded_dry_runs == {"migrate": False, "clear_cache": False}


def test_running_the_module_as_a_script_invokes_main(monkeypatch, caplog) -> None:
    class _Cache:
        def count_documents(self, query):
            return 3

    class _Database:
        name = "ebl_migrate_probe"

        def list_collection_names(self):
            return []

        def __getitem__(self, name):
            return _Cache()

    class _Client:
        def __init__(self, uri):
            self.uri = uri

        def get_database(self, name):
            return _Database()

    monkeypatch.setattr(pymongo, "MongoClient", _Client)
    monkeypatch.setenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
    monkeypatch.setenv("MONGODB_DB", "ebl_migrate_probe")
    monkeypatch.setattr(sys, "argv", [MODULE])
    monkeypatch.delitem(sys.modules, MODULE, raising=False)

    with caplog.at_level(logging.INFO):
        runpy.run_module(MODULE, run_name="__main__")

    assert "fragments: no such collection in database 'ebl_migrate_probe'" in (
        caplog.text
    )
    assert "cache: 3 entries would be cleared" in caplog.text
