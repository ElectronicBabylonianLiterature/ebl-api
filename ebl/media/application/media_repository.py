from abc import ABC, abstractmethod
from typing import Mapping, Optional, Sequence

from ebl.media.application.media_stored import StoredMedia
from ebl.media.domain import Media, MediaId, MediaImportSource
from ebl.transliteration.domain.museum_number import MuseumNumber


class MediaReader(ABC):
    @abstractmethod
    def find_by_id(self, media_id: MediaId) -> Optional[Media]:
        """Return the current domain state, or None when no such media exists."""
        raise NotImplementedError

    @abstractmethod
    def find_stored_by_id(self, media_id: MediaId) -> Optional[StoredMedia]:
        """Return the same current domain state plus its current stored handles.

        Must be consistent with `find_by_id`: both describe one current state.
        """
        raise NotImplementedError

    @abstractmethod
    def find_by_import_source(
        self, import_source: MediaImportSource
    ) -> Optional[Media]:
        """Return the media with this complete import identity, or None."""
        raise NotImplementedError

    @abstractmethod
    def find_by_fragment(self, fragment_id: MuseumNumber) -> Sequence[Media]:
        """Return only media associated with `fragment_id`, in canonical order.

        Canonical order is the association's sort order for this fragment, then
        media id. Returns an empty sequence when the fragment has no media.
        """
        raise NotImplementedError

    @abstractmethod
    def find_by_fragments(
        self, fragment_ids: Sequence[MuseumNumber]
    ) -> Mapping[MuseumNumber, Sequence[Media]]:
        """Resolve every requested fragment in one batch operation.

        Every requested fragment appears as a key; fragments with no media map
        to an empty sequence. Duplicate inputs yield one key. Each sequence uses
        that fragment's canonical order. Implementations must not issue one
        query per fragment.
        """
        raise NotImplementedError

    @abstractmethod
    def find_in_fragment(
        self, media_id: MediaId, fragment_id: MuseumNumber
    ) -> Optional[Media]:
        """Return the media only when it is associated with `fragment_id`.

        Returns None when the media does not exist *or* is not associated with
        that fragment. The fragment argument is an object-scoping boundary and
        must never be ignored: returning media associated only with another
        fragment is an IDOR defect. The web layer must authenticate and
        authorize the caller before invoking this repository operation.
        """
        raise NotImplementedError

    @abstractmethod
    def find_stored_in_fragment(
        self, media_id: MediaId, fragment_id: MuseumNumber
    ) -> Optional[StoredMedia]:
        """Stored-state form of `find_in_fragment`, with the same fragment rule.

        Binary routes resolve current handles through this method, so ignoring
        the fragment argument would expose another fragment's binaries.
        """
        raise NotImplementedError

    @abstractmethod
    def find_primary_media(self, fragment_id: MuseumNumber) -> Optional[Media]:
        """Primary media for the fragment, preferring a primary PHOTO.

        The first primary PHOTO in canonical order, else the first primary media
        of any type, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def find_primary_photo(self, fragment_id: MuseumNumber) -> Optional[Media]:
        """First primary PHOTO in canonical order, or None. Never returns a COPY."""
        raise NotImplementedError


class MediaWriter(ABC):
    @abstractmethod
    def set_primary(
        self, fragment_id: MuseumNumber, media_id: MediaId
    ) -> Sequence[Media]:
        """Atomically promote one associated media and demote all its peers.

        Raises `MediaNotFoundError` when the target is absent or outside the
        fragment. The read, validation, and complete transition occur in one
        repository operation so concurrent writers cannot leave stale or
        multiple primary flags. Stored handles remain unchanged.
        """
        raise NotImplementedError

    @abstractmethod
    def create(self, media: StoredMedia) -> MediaId:
        """Insert complete stored state; never update.

        Raises `MediaAlreadyExistsError` when the media id or non-null import
        source is already present. Both uniqueness checks and insertion are one
        atomic operation so concurrent imports cannot create duplicate sources.
        """
        raise NotImplementedError

    @abstractmethod
    def replace(self, media: StoredMedia) -> StoredMedia:
        """Atomically replace one media's whole stored state; return the PREVIOUS state.

        The target must already exist, otherwise `MediaNotFoundError` is raised.
        Media identity is preserved. Domain metadata and stored handle
        references switch together, so no partial current state is observable.
        A non-null import source remains unique across all media, checked in the
        same atomic operation as the replacement.

        The return value is the state that was current *before* this call. Only
        `previous.superseded_by(replacement)` may be deleted afterwards; the
        previous handle set itself must never be deleted wholesale, because a
        metadata-only replacement keeps every handle current.
        """
        raise NotImplementedError

    @abstractmethod
    def replace_many(self, media: Sequence[StoredMedia]) -> Sequence[StoredMedia]:
        """Atomically replace several media; return their previous states in order.

        All targets are validated before anything mutates: duplicate media ids
        and duplicate non-null import sources are rejected, and every target
        must already exist. Either every replacement is applied or none is.

        The result is positional: index `i` is the state that was current before
        `media[i]` was applied, so callers may pair `previous[i]` with
        `media[i]`. An empty sequence is valid and is a no-op that mutates
        nothing and returns an empty sequence; it is never an error.

        Intended for metadata-only transitions; it implies no binary cleanup.
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, media_id: MediaId) -> Optional[StoredMedia]:
        """Atomically hide metadata and retain its stored state for cleanup.

        Repeated calls return the same tombstoned state until `finish_delete`.
        Creation with the same media id is rejected while that tombstone exists.
        This makes exact-handle binary cleanup retryable without allowing a
        retry to delete a newly created generation.
        """
        raise NotImplementedError

    @abstractmethod
    def finish_delete(self, media: StoredMedia) -> None:
        """Discard this exact tombstone after all its handles are deleted.

        A stale completion is a no-op when a newer deletion generation exists.
        """
        raise NotImplementedError


class MediaRepository(MediaReader, MediaWriter, ABC):
    pass
