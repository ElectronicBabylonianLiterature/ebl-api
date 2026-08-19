from abc import ABC, abstractmethod
from typing import Mapping, Optional, Sequence

from ebl.media.application.media_stored import StoredMedia
from ebl.media.domain import Media, MediaId
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
        that fragment. The fragment argument is an authorization boundary and
        must never be ignored: returning media associated only with another
        fragment is an IDOR defect.
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
    def create(self, media: StoredMedia) -> MediaId:
        """Insert complete stored state; never update.

        Raises `MediaAlreadyExistsError` when the media id is already present.
        """
        raise NotImplementedError

    @abstractmethod
    def replace(self, media: StoredMedia) -> StoredMedia:
        """Atomically replace one media's whole stored state; return the PREVIOUS state.

        The target must already exist, otherwise `MediaNotFoundError` is raised.
        Media identity is preserved. Domain metadata and stored handle
        references switch together, so no partial current state is observable.

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
        are rejected and every target must already exist. Either every
        replacement is applied or none is, so a caller cannot observe a
        half-applied per-fragment primary transition.

        Intended for metadata-only transitions; it implies no binary cleanup.
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, media_id: MediaId) -> None:
        """Delete media metadata only; idempotent, and a no-op when absent.

        Stored binaries are removed separately, after this succeeds.
        """
        raise NotImplementedError


class MediaRepository(MediaReader, MediaWriter, ABC):
    pass
