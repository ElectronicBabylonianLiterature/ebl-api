from typing import BinaryIO, Callable, Iterator, Mapping

import attr

from ebl.media.infrastructure.backfill_candidates import (
    candidate_media,
    existing_outcome,
    initial_candidate,
    inspect_candidate,
)
from ebl.media.application.backfill_plan import (
    BackfillPolicy,
    PlannedPhoto,
    SourceRejected,
)
from ebl.media.application.media_errors import MediaAlreadyExistsError
from ebl.media.application.media_requests import BackfillRequest
from ebl.media.application.media_stored import StoredMedia, StoredMediaRepresentations
from ebl.media.application.media_storage_identity import StoredRepresentationHandle
from ebl.media.infrastructure.backfill_images import source_content
from ebl.media.infrastructure.backfill_previews import PreviewWriter
from ebl.media.infrastructure.backfill_preflight import assert_apply_ready
from ebl.media.infrastructure.backfill_sources import (
    LegacyPhotoSources,
    decode_source_id,
)
from ebl.media.infrastructure.grid_fs_media_representation_store import (
    GridFsMediaRepresentationStore,
)
from ebl.media.infrastructure.mongo_media_repository import MongoMediaRepository
from ebl.media.infrastructure.legacy_media_handles import LegacyRepresentationAdoption


class LegacyPhotoMigration:
    def __init__(
        self,
        sources: LegacyPhotoSources,
        repository: MongoMediaRepository,
        store: GridFsMediaRepresentationStore,
        policy: BackfillPolicy,
    ) -> None:
        self.sources = sources
        self.repository = repository
        self.store = store
        self.policy = policy
        self._apply_ready = False

    def plan_batch(self, request: BackfillRequest) -> Iterator[PlannedPhoto]:
        if not request.dry_run:
            raise ValueError("Planning must use a dry-run request.")
        for document in self.sources.batch(request):
            try:
                self.sources.mapping(document)
                with source_content(
                    self.sources.database, document, self.policy
                ) as content:
                    candidate = inspect_candidate(
                        document, content, self.sources, self.policy
                    )
                outcome = existing_outcome(candidate, self.repository)
                yield attr.evolve(candidate, outcome=outcome or candidate.outcome)
            except SourceRejected as error:
                yield attr.evolve(
                    initial_candidate(document),
                    outcome=error.outcome,
                    reason=error.reason,
                )

    def apply(
        self,
        expected: PlannedPhoto,
        on_staged: Callable[[StoredRepresentationHandle], None] | None = None,
    ) -> PlannedPhoto:
        if expected.outcome not in {"candidate", "already-present"}:
            return expected
        if not self._apply_ready:
            self.repository.assert_writable_topology()
            assert_apply_ready(self.sources.database)
            self._apply_ready = True
        try:
            document = self._current_document(expected)
            with source_content(
                self.sources.database, document, self.policy
            ) as content:
                current = inspect_candidate(
                    document, content, self.sources, self.policy
                )
                if attr.evolve(expected, outcome="candidate") != current:
                    raise SourceRejected("conflicting", "source-changed-since-plan")
                outcome = existing_outcome(current, self.repository)
                if outcome is not None:
                    return attr.evolve(current, outcome=outcome)
                return self._create(current, document, content, on_staged)
        except SourceRejected as error:
            return attr.evolve(expected, outcome="conflicting", reason=error.reason)

    def _current_document(self, expected: PlannedPhoto) -> dict:
        document = self.sources.files.find_one(
            {"_id": decode_source_id(expected.source_id)}
        )
        if document is None:
            raise SourceRejected("conflicting", "source-removed")
        return document

    def _create(
        self,
        candidate: PlannedPhoto,
        document: Mapping,
        content: BinaryIO,
        on_staged: Callable[[StoredRepresentationHandle], None] | None,
    ) -> PlannedPhoto:
        media = candidate_media(candidate)
        original = self.store.adopt_legacy(
            LegacyRepresentationAdoption(
                media.id,
                "photos",
                document["_id"],
                media.representations.original,
            )
        )
        previews = PreviewWriter(self.store, on_staged)
        try:
            stored = (
                previews.create(media, original, content)
                if self.policy.generate_previews
                and candidate.reason != "preview-deferred-pixel-limit"
                else StoredMedia(media, StoredMediaRepresentations(original))
            )
            if not self.sources.unchanged(document):
                raise SourceRejected("conflicting", "source-metadata-changed")
            self.sources.mapping(document)
        except BaseException:
            self._cleanup(previews.handles)
            raise
        try:
            self.repository.create(stored)
        except MediaAlreadyExistsError:
            self._cleanup(previews.handles)
            return attr.evolve(
                candidate,
                outcome=existing_outcome(candidate, self.repository) or "conflicting",
            )
        return attr.evolve(candidate, outcome="created")

    def _cleanup(self, handles: list[StoredRepresentationHandle]) -> None:
        for handle in handles:
            self.store.delete_representation(handle)

    def reconcile_staged(
        self, candidate: PlannedPhoto, handles: list[StoredRepresentationHandle]
    ) -> None:
        media = candidate_media(candidate)
        source_owner = (
            self.repository.find_by_import_source(media.import_source)
            if media.import_source is not None
            else None
        )
        stored = self.repository.find_stored_by_id(
            source_owner.id if source_owner is not None else media.id
        )
        if stored is None:
            raise ValueError(
                "Staged preview reconciliation needs acknowledged current media."
            )
        current = set(stored.representations.handles)
        deterministic_owner = self.repository.find_stored_by_id(media.id)
        if deterministic_owner is not None:
            current.update(deterministic_owner.representations.handles)
        for handle in handles:
            if handle.media_id != media.id:
                raise ValueError("Staged preview owner differs from candidate media.")
            if handle not in current:
                self.store.delete_representation(handle)
