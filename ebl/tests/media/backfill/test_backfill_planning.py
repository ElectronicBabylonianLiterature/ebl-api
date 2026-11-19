from collections.abc import Callable

import pytest
from pymongo.database import Database

from ebl.media.application.backfill_plan import BackfillPolicy, PlannedPhoto
from ebl.media.application.media_requests import BackfillRequest
from ebl.tests.media.backfill.conftest import image_bytes


def test_dry_run_is_read_only(
    database: Database, legacy_photo: Callable, migration_factory: Callable
) -> None:
    legacy_photo()
    before = {
        name: list(database[name].find()) for name in database.list_collection_names()
    }
    migration = migration_factory(initialize=False)
    result = tuple(migration.plan_batch(BackfillRequest()))
    assert len(result) == 1
    assert result[0].outcome == "candidate"
    assert result[0].fragment_id == "K.1"
    assert result[0].representation is not None
    assert PlannedPhoto.of(result[0].document()) == result[0]
    after = {
        name: list(database[name].find()) for name in database.list_collection_names()
    }
    assert after == before


@pytest.mark.parametrize(
    "case",
    [
        ("K.1.jpg", b"broken", True, "malformed-original"),
        ("K.1.jpg", image_bytes()[:-2], True, "malformed-original"),
        ("K.1.tiff", None, True, "unsupported-filename"),
        ("bad.jpg", None, True, "ambiguous-filename"),
        ("K.1.jpg", None, False, "unknown-or-ambiguous-fragment"),
        ("K.1.jpg", image_bytes("TIFF"), True, "unsupported-mime-type"),
    ],
)
def test_blocked_sources(
    legacy_photo: Callable,
    migration_factory: Callable,
    case: tuple[str, bytes | None, bool, str],
) -> None:
    filename, content, create_fragment, reason = case
    legacy_photo(filename=filename, content=content, create_fragment=create_fragment)
    result = tuple(migration_factory().plan_batch(BackfillRequest()))
    assert result[0].outcome == "blocked"
    assert result[0].reason == reason


def test_competing_extensions_are_not_selected(
    legacy_photo: Callable, migration_factory: Callable
) -> None:
    legacy_photo()
    legacy_photo(filename="K.1.png", content=image_bytes("PNG"))
    results = tuple(migration_factory().plan_batch(BackfillRequest()))
    assert {result.reason for result in results} == {"multiple-originals"}
    assert all(result.outcome == "review" for result in results)


def test_pixel_limit_is_review_not_corruption(
    legacy_photo: Callable, migration_factory: Callable
) -> None:
    legacy_photo(content=image_bytes("PNG"))
    migration = migration_factory(BackfillPolicy(max_pixels=10))
    result = tuple(migration.plan_batch(BackfillRequest()))[0]
    assert (result.outcome, result.reason) == ("review", "pixel-inspection-limit")


def test_batch_resume_keeps_typed_ids(
    legacy_photo: Callable, migration_factory: Callable
) -> None:
    from bson import ObjectId

    identifier = ObjectId()
    legacy_photo(file_id=identifier)
    legacy_photo(file_id=str(identifier))
    migration = migration_factory()
    first = tuple(migration.plan_batch(BackfillRequest(batch_size=1)))
    second = tuple(
        migration.plan_batch(
            BackfillRequest(batch_size=1, resume_after=first[0].source_id)
        )
    )
    assert first[0].source_id != second[0].source_id
    assert len(second) == 1
    assert not tuple(
        migration.plan_batch(
            BackfillRequest(batch_size=1, resume_after=second[0].source_id)
        )
    )


def test_unavailable_chunks_are_blocked(
    database: Database, legacy_photo: Callable, migration_factory: Callable
) -> None:
    document = legacy_photo()
    database["photos.chunks"].delete_many({"files_id": document["_id"]})
    result = tuple(migration_factory().plan_batch(BackfillRequest()))[0]
    assert result.outcome == "blocked"
    assert result.reason == "unavailable-original"
