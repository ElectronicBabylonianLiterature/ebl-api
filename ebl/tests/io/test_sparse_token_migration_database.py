from typing import Any, Dict, List, Tuple, cast

import pytest
from pymongo.database import Database

from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.fragmentarium.infrastructure.mongo_fragment_repository import (
    MongoFragmentRepository,
)
from ebl.io.sparse_tokens.migrate import clear_cache, migrate
from ebl.io.sparse_tokens.report import CollectionReport
from ebl.provenance.application.provenance_service import ProvenanceService
from ebl.tests.fragmentarium.stored_line_shapes import legacy_shape, sparse_tokens
from ebl.tests.io.sparse_token_migration_fixtures import (
    CHAPTER,
    FRAGMENT,
    full_chapter_document,
    full_fragment_document,
    insert_full_documents,
    stored_chapter,
    stored_fragment,
)
from ebl.transliteration.application.text_schema import TextSchema
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark


@pytest.fixture
def full_database(
    database: Database, seeded_provenance_service: ProvenanceService
) -> Database:
    insert_full_documents(database, seeded_provenance_service)
    return database


def counts(reports: List[CollectionReport]) -> Dict[str, Tuple[int, int]]:
    return {report.collection: (report.changed, report.written) for report in reports}


def test_a_dry_run_reports_changes_and_writes_nothing(full_database: Database) -> None:
    before = (stored_fragment(full_database), stored_chapter(full_database))

    reports = migrate(full_database, apply=False)

    assert counts(reports) == {"fragments": (1, 0), "chapters": (1, 0)}
    assert (stored_fragment(full_database), stored_chapter(full_database)) == before
    assert all(report.bytes_after < report.bytes_before for report in reports)


def test_apply_stores_the_sparse_shape(
    full_database: Database, seeded_provenance_service: ProvenanceService
) -> None:
    full_fragment = full_fragment_document(FRAGMENT, seeded_provenance_service)
    full_chapter = full_chapter_document(CHAPTER)

    reports = migrate(full_database, apply=True)

    assert counts(reports) == {"fragments": (1, 1), "chapters": (1, 1)}
    assert stored_fragment(full_database)["text"] == sparse_tokens(
        full_fragment["text"]
    )
    for field in ("lines", "manuscripts"):
        assert stored_chapter(full_database)[field] == sparse_tokens(
            full_chapter[field]
        )


def test_apply_keeps_the_domain_objects(
    full_database: Database,
    fragment_repository: MongoFragmentRepository,
    text_repository: MongoTextRepository,
) -> None:
    fragment = fragment_repository.query_by_museum_number(FRAGMENT.number)
    chapter = text_repository.find_chapter(CHAPTER.id_)

    migrate(full_database, apply=True)

    assert fragment_repository.query_by_museum_number(FRAGMENT.number) == fragment
    assert text_repository.find_chapter(CHAPTER.id_) == chapter
    assert fragment.text == FRAGMENT.text
    assert chapter.lines == CHAPTER.lines


def test_apply_leaves_other_fields_alone(full_database: Database) -> None:
    full_database.fragments.update_one({}, {"$set": {"_sortKey": 7}})
    signs = stored_chapter(full_database)["signs"]

    migrate(full_database, apply=True)

    assert stored_fragment(full_database)["_sortKey"] == 7
    assert stored_chapter(full_database)["signs"] == signs


@pytest.mark.parametrize("full_check", [False, True])
def test_a_second_run_finds_nothing_to_change(
    full_database: Database, full_check: bool
) -> None:
    migrate(full_database, apply=True)

    reports = migrate(full_database, apply=False, full_check=full_check)

    assert counts(reports) == {"fragments": (0, 0), "chapters": (0, 0)}
    assert [report.unchanged for report in reports] == [1, 1]


def test_a_malformed_document_without_defaults_is_skipped(
    full_database: Database,
) -> None:
    full_database.fragments.update_one({}, {"$set": {"text.lines": "not lines"}})

    [report, _] = migrate(full_database, apply=True)

    assert (report.unchanged, report.unreadable) == (1, {})


def test_enclosure_type_order_alone_is_not_a_change(full_database: Database) -> None:
    migrate(full_database, apply=True)
    text = stored_fragment(full_database)["text"]
    reversed_text = reverse_enclosure_types(text)
    full_database.fragments.update_one({}, {"$set": {"text": reversed_text}})

    reports = migrate(full_database, apply=False, collections=["fragments"])

    assert counts(reports) == {"fragments": (0, 0)}


def reverse_enclosure_types(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: list(reversed(item))
            if key == "enclosureType"
            else reverse_enclosure_types(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [reverse_enclosure_types(item) for item in value]
    return value


def test_apply_splits_legacy_names(
    database: Database, seeded_provenance_service: ProvenanceService
) -> None:
    full = full_fragment_document(FRAGMENT, seeded_provenance_service)
    database.fragments.insert_one({**full, "text": legacy_shape(full["text"])})

    migrate(database, apply=True)

    assert stored_fragment(database)["text"] == sparse_tokens(full["text"])


def test_a_fragment_without_text_is_left_alone(
    database: Database, seeded_provenance_service: ProvenanceService
) -> None:
    full = full_fragment_document(FRAGMENT, seeded_provenance_service)
    database.fragments.insert_one({key: full[key] for key in full if key != "text"})

    [report] = migrate(database, apply=True)

    assert (report.scanned, report.unchanged, report.changed) == (1, 1, 0)


def test_an_unreadable_document_is_reported_and_left_alone(
    full_database: Database,
) -> None:
    full_database.fragments.update_one({}, {"$set": {"text.lines": "not lines"}})

    [report, _] = migrate(full_database, apply=True, full_check=True)

    assert list(report.unreadable) == [str(FRAGMENT.number)]
    assert report.has_problems
    assert stored_fragment(full_database)["text"]["lines"] == "not lines"


def test_an_unknown_token_key_makes_the_document_unreadable(
    full_database: Database,
) -> None:
    full_database.fragments.update_one(
        {}, {"$set": {"text.lines.0.content.0.unknownKey": 1}}
    )

    [report, _] = migrate(full_database, apply=True)

    assert list(report.unreadable) == [str(FRAGMENT.number)]
    assert report.written == 0


def test_a_token_key_the_schema_drops_is_reported(database: Database) -> None:
    text = cast(dict, TextSchema().dump(parse_atf_lark("1. ku")))
    text["lines"][0]["content"][0]["parts"][0]["nameParts"][0]["unknownKey"] = 1
    database.fragments.insert_one({"_id": "X.9", "text": text})

    [report] = migrate(database, apply=True)

    assert report.dropped_keys == {"X.9": ["unknownKey"]}
    assert report.written == 0


def test_an_oversized_document_is_reported(
    full_database: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("ebl.io.sparse_tokens.migrate.MAX_BSON_SIZE", 10)

    reports = migrate(full_database, apply=True)

    assert [len(report.oversized) for report in reports] == [1, 1]
    assert [report.written for report in reports] == [0, 0]


def test_a_missing_collection_is_skipped(
    database: Database, caplog: pytest.LogCaptureFixture
) -> None:
    assert migrate(database, apply=True) == []
    assert "fragments: no such collection" in caplog.text


@pytest.mark.parametrize("apply,remaining", [(False, 2), (True, 0)])
def test_clear_cache(database: Database, apply: bool, remaining: int) -> None:
    database.cache.insert_many([{"key": 1}, {"key": 2}])

    assert clear_cache(database, apply) == 2
    assert database.cache.count_documents({}) == remaining


def test_a_dropped_key_outside_tokens_is_reported(database: Database) -> None:
    text = cast(dict, TextSchema().dump(parse_atf_lark("1-2. ku")))
    text["lines"][0]["lineNumber"]["start"]["unknownKey"] = 1
    database.fragments.insert_one({"_id": "X.9", "text": text})

    [report] = migrate(database, apply=True)

    assert report.dropped_keys == {"X.9": ["unknownKey"]}
    assert report.written == 0


def test_a_chapter_without_lines_is_unreadable(full_database: Database) -> None:
    full_database.chapters.update_one({}, {"$unset": {"lines": ""}})

    [_, report] = migrate(full_database, apply=True)

    assert list(report.unreadable.values()) == ["MissingFields: missing lines"]
    assert report.has_problems
