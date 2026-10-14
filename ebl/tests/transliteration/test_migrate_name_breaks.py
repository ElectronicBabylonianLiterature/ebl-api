import logging
import runpy
import sys

import pymongo
import pytest

from ebl.tests.transliteration.legacy_named_sign import (
    LATER_NAMED_SIGN_PATH,
    LEGACY_PART,
    MODULE,
    NAMED_SIGN_PATH,
    legacy_fragment,
    legacy_fragment_with_a_later_name,
    legacy_name,
)
from ebl.transliteration.migrate_name_breaks import (
    LegacyName,
    find_legacy_names,
    get_database,
    main,
)


def _paths(document: object) -> list[str]:
    return [name.path for name in find_legacy_names(document)]


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


def test_get_database_uses_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
    monkeypatch.setenv("MONGODB_DB", "ebl_migrate_name_breaks_probe")

    database = get_database()

    assert database.name == "ebl_migrate_name_breaks_probe"
    database.client.close()


def test_get_database_requires_the_database_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
    monkeypatch.delenv("MONGODB_DB", raising=False)

    with pytest.raises(KeyError, match="MONGODB_DB"):
        get_database()


@pytest.fixture
def recorded_calls(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, bool]]:
    calls: list[tuple[str, bool]] = []

    def fake_migrate(database: object, dry_run: bool) -> dict[str, int]:
        calls.append(("migrate", dry_run))
        return {}

    def fake_clear_cache(database: object, dry_run: bool) -> int:
        calls.append(("clear_cache", dry_run))
        return 0

    monkeypatch.setattr(MODULE + ".migrate", fake_migrate)
    monkeypatch.setattr(MODULE + ".clear_cache", fake_clear_cache)
    monkeypatch.setattr(MODULE + ".get_database", lambda: None)
    return calls


def test_main_defaults_to_a_dry_run(recorded_calls: list[tuple[str, bool]]) -> None:
    main([])

    assert recorded_calls == [("clear_cache", True), ("migrate", True)]


def test_main_clears_the_cache_before_migrating_when_applying(
    recorded_calls: list[tuple[str, bool]],
) -> None:
    main(["--apply"])

    assert recorded_calls == [("clear_cache", False), ("migrate", False)]


def test_running_the_module_as_a_script_invokes_main(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    class _Cache:
        def count_documents(self, query: object) -> int:
            return 3

    class _Database:
        name = "ebl_migrate_probe"

        def list_collection_names(self) -> list[str]:
            return []

        def __getitem__(self, name: str) -> _Cache:
            return _Cache()

    class _Client:
        def __init__(self, uri: str) -> None:
            self.uri = uri

        def get_database(self, name: str) -> _Database:
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
