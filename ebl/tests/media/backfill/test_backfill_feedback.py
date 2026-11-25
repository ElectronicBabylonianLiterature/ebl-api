from collections.abc import Callable
from pathlib import Path
from tempfile import SpooledTemporaryFile
from typing import BinaryIO, cast

import attr
import pytest
from bson import ObjectId
from pymongo.database import Database

from ebl.io.media import backfill
from ebl.media.application.backfill_plan import BackfillPolicy
from ebl.media.application.media_requests import BackfillRequest
from ebl.media.application.media_storage_identity import StoredRepresentationHandle
from ebl.media.infrastructure import backfill_images
from ebl.media.infrastructure.backfill_candidates import candidate_media
from ebl.media.infrastructure.backfill_sources import encode_source_id


def test_object_id_and_string_source_ids_produce_distinct_media(
    legacy_photo: Callable, migration_factory: Callable
) -> None:
    identifier = ObjectId()
    legacy_photo(file_id=identifier)
    candidate = tuple(migration_factory().plan_batch(BackfillRequest()))[0]
    object_media = candidate_media(candidate)
    string_media = candidate_media(
        attr.evolve(candidate, source_id=encode_source_id(str(identifier)))
    )
    assert object_media.id != string_media.id
    assert object_media.import_source != string_media.import_source


def test_legacy_adoption_is_staged_before_later_source_conflict(
    database: Database,
    legacy_photo: Callable,
    migration_factory: Callable,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    legacy_photo()
    migration = migration_factory(BackfillPolicy(generate_previews=False))
    candidate = tuple(migration.plan_batch(BackfillRequest()))[0]
    validations = iter([True, True, False])
    monkeypatch.setattr(
        migration.sources, "unchanged", lambda _document: next(validations)
    )
    staged: list[StoredRepresentationHandle] = []
    result = migration.apply(candidate, staged.append)
    assert result.reason == "source-metadata-changed"
    assert len(staged) == 1
    assert staged[0].media_id == candidate_media(candidate).id
    assert database["mediaFiles"].find_one({"_id": staged[0].value}) is not None
    assert database["media"].count_documents({}) == 0
    assert database["photos.files"].count_documents({}) == 1


def test_source_spool_uses_requested_durable_directory(
    database: Database,
    legacy_photo: Callable,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    document = legacy_photo()
    directories: list[str | None] = []

    def spool(*, max_size: int, mode: str, dir: str | None) -> BinaryIO:
        directories.append(dir)
        return cast(
            BinaryIO, SpooledTemporaryFile(max_size=max_size, mode=mode, dir=dir)
        )

    monkeypatch.setattr(backfill_images, "SpooledTemporaryFile", spool)
    with backfill_images.source_content(
        database, document, BackfillPolicy(), tmp_path
    ) as content:
        assert content.read()
    assert directories == [str(tmp_path)]


def test_operator_result_shows_sanitized_endpoint(
    database: Database,
    legacy_photo: Callable,
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
) -> None:
    legacy_photo()
    status = backfill.main(
        [
            "dry-run",
            "--database",
            database.name,
            "--uri-env",
            "MEDIA_TEST_URI",
            "--report",
            str(tmp_path / "plan.jsonl"),
        ]
    )
    assert status == 0
    output, _error = cast(tuple[str, str], capsys.readouterr())
    assert '"endpoint": "127.0.0.1:' in output or '"endpoint": "localhost:' in output
    assert database.name in output
