from abc import ABC, abstractmethod
from typing import Mapping, Optional, Sequence

from ebl.media.application.media_requests import (
    BackfillReport,
    BackfillRequest,
    ImportReport,
    ImportRequest,
)
from ebl.media.application.media_stored import StoredMedia
from ebl.media.domain import Media, MediaId
from ebl.transliteration.domain.museum_number import MuseumNumber


class MediaService(ABC):
    @abstractmethod
    def list_fragment_media(self, fragment_id: MuseumNumber) -> Sequence[Media]:
        """Fragment's media in canonical order."""
        raise NotImplementedError

    @abstractmethod
    def find_media_by_fragments(
        self, fragment_ids: Sequence[MuseumNumber]
    ) -> Mapping[MuseumNumber, Sequence[Media]]:
        """One batch read keyed by every requested fragment."""
        raise NotImplementedError

    @abstractmethod
    def get_fragment_media(
        self, fragment_id: MuseumNumber, media_id: MediaId
    ) -> Optional[Media]:
        """Media within the fragment context, or None when not associated."""
        raise NotImplementedError

    @abstractmethod
    def get_stored_fragment_media(
        self, fragment_id: MuseumNumber, media_id: MediaId
    ) -> Optional[StoredMedia]:
        """Stored state within the fragment context, or None when not associated."""
        raise NotImplementedError

    @abstractmethod
    def set_primary_media(
        self, fragment_id: MuseumNumber, media_id: MediaId
    ) -> Sequence[Media]:
        """Promote one media and demote the fragment's others, atomically.

        Rejects a target not associated with the fragment. Delegates the whole
        transition to one atomic repository operation so concurrent callers
        cannot leave stale or multiple primary flags. Stored representation
        handles are unchanged and associations with other fragments are kept.
        """
        raise NotImplementedError

    @abstractmethod
    def delete_media(self, media_id: MediaId) -> None:
        """Tombstone metadata, delete its exact handles, then finish deletion.

        A failed binary delete leaves the tombstone available to a retry, while
        ordinary reads no longer expose metadata pointing at missing bytes.
        """
        raise NotImplementedError


class MediaImporter(ABC):
    @abstractmethod
    def import_media(self, request: ImportRequest) -> ImportReport:
        """Import media for a source, honouring `request.mode`.

        When `request.dry_run` is true the call MUST NOT mutate anything: no
        `write_original`, `write_display` or `write_thumbnail`; no `create`,
        `replace`, `replace_many` or `delete`; no `delete_representation`; no
        association or primary change. No binary
        may even be staged. Reads, validation, MIME inspection, duplicate
        detection and reporting are allowed, and the report must describe what
        the same request would have done with `dry_run` false.
        """
        raise NotImplementedError


class MediaBackfill(ABC):
    @abstractmethod
    def backfill(self, request: BackfillRequest) -> BackfillReport:
        """Create media metadata for legacy files without modifying them.

        Honours `request.dry_run` with the same zero-mutation rule as
        `MediaImporter.import_media`. Processes at most one bounded batch,
        starting after `request.resume_after`, and returns
        `BackfillReport.next_resume_token` so the caller can continue; the token
        is None once the scan is complete.
        """
        raise NotImplementedError
