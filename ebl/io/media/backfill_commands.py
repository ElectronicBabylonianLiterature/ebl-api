from pathlib import Path
from functools import partial
from typing import Mapping

import attr

from ebl.io.media.backfill_journal import BackfillJournal
from ebl.io.media.backfill_plan_file import plan_rows, verified_plan
from ebl.media.application.backfill_plan import BackfillPolicy, PlannedPhoto
from ebl.media.application.media_requests import BackfillRequest
from ebl.media.infrastructure.backfill_runner import LegacyPhotoMigration
from ebl.media.infrastructure.media_documents import handle_document, load_handle
from ebl.media.application.media_storage_identity import StoredRepresentationHandle


def record_staged(
    journal: BackfillJournal, source_id: str, handle: StoredRepresentationHandle
) -> None:
    journal.stage(source_id, handle_document(handle))


@attr.s(auto_attribs=True, frozen=True)
class MigrationRunOptions:
    report: Path
    target: Mapping
    resume: bool = False
    batch_size: int = 100
    max_batches: int | None = None
    limit: int | None = None


def dry_run(migration: LegacyPhotoMigration, options: MigrationRunOptions) -> dict:
    header = dict(options.target, command="dry-run", policy=migration.policy.document())
    with BackfillJournal(options.report, header, options.resume) as journal:
        batches = 0
        while not journal.completed and (
            options.max_batches is None or batches < options.max_batches
        ):
            request = BackfillRequest(
                batch_size=options.batch_size, resume_after=journal.last_source
            )
            scanned = 0
            for candidate in migration.plan_batch(request):
                journal.append(candidate.document())
                scanned += 1
            batches += 1
            if scanned < options.batch_size:
                journal.finish()
        return {"complete": journal.completed, "counts": dict(journal.counts)}


def apply_plan(
    migration: LegacyPhotoMigration, plan: Path, options: MigrationRunOptions
) -> dict:
    with verified_plan(plan) as (snapshot, header, digest):
        return _apply_verified(migration, (snapshot, header, digest), options)


def _apply_verified(
    migration: LegacyPhotoMigration,
    verified: tuple[Path, Mapping, str],
    options: MigrationRunOptions,
) -> dict:
    plan, header, digest = verified
    if any(header.get(key) != value for key, value in options.target.items()):
        raise ValueError("Plan belongs to another database or endpoint.")
    if BackfillPolicy.of(header["policy"]) != migration.policy:
        raise ValueError("Apply policy must equal the dry-run policy.")
    report_header = dict(
        options.target,
        command="apply",
        policy=migration.policy.document(),
        planSha256=digest,
    )
    with BackfillJournal(options.report, report_header, options.resume) as journal:
        if not journal.completed:
            processed = 0
            for document in plan_rows(plan, journal.last_source):
                if options.limit is not None and processed >= options.limit:
                    break
                candidate = PlannedPhoto.of(document)

                result = migration.apply(
                    candidate, partial(record_staged, journal, candidate.source_id)
                )
                if (
                    result.outcome in {"created", "already-present"}
                    and candidate.source_id in journal.pending
                ):
                    migration.reconcile_staged(
                        candidate,
                        [
                            load_handle(handle)
                            for handle in journal.pending[candidate.source_id]
                        ],
                    )
                    journal.reconcile(candidate.source_id)
                journal.append(result.document())
                processed += 1
            else:
                journal.finish()
        return {
            "complete": journal.completed,
            "counts": dict(journal.counts),
            "pendingSources": sorted(journal.pending),
        }
