from typing import Dict, List, Mapping, Optional, Sequence

import attr

from ebl.media.application import (
    MediaAlreadyExistsError,
    MediaNotFoundError,
    MediaRepository,
    StoredMedia,
    fragment_media_in_order,
    primary_media_for,
    primary_photo_for,
    with_primary,
)
from ebl.media.domain import Media, MediaId, MediaImportSource
from ebl.tests.media.in_memory_media_validation import require_unique_import_sources
from ebl.tests.media.in_memory_representation_store import (
    InMemoryRepresentationStore as InMemoryRepresentationStore,
)
from ebl.transliteration.domain.museum_number import MuseumNumber

__all__ = ["InMemoryMediaRepository", "InMemoryRepresentationStore"]


class InMemoryMediaRepository(MediaRepository):
    def __init__(
        self,
        media: Sequence[StoredMedia] = (),
        call_log: Optional[List[str]] = None,
    ) -> None:
        self.fail_next_replace = False
        self.call_log = call_log if call_log is not None else []
        self._media: Dict[MediaId, StoredMedia] = {
            stored_media.media.id: stored_media for stored_media in media
        }
        self._deleting: Dict[MediaId, StoredMedia] = {}

    def find_by_id(self, media_id: MediaId) -> Optional[Media]:
        stored_media = self.find_stored_by_id(media_id)
        return stored_media.media if stored_media is not None else None

    def find_stored_by_id(self, media_id: MediaId) -> Optional[StoredMedia]:
        return self._media.get(media_id)

    def find_by_import_source(
        self, import_source: MediaImportSource
    ) -> Optional[Media]:
        return next(
            (
                item.media
                for item in self._media.values()
                if item.media.import_source == import_source
            ),
            None,
        )

    def find_by_fragment(self, fragment_id: MuseumNumber) -> Sequence[Media]:
        return fragment_media_in_order(
            fragment_id,
            tuple(
                item.media
                for item in self._media.values()
                if item.media.is_associated_with(fragment_id)
            ),
        )

    def find_by_fragments(
        self, fragment_ids: Sequence[MuseumNumber]
    ) -> Mapping[MuseumNumber, Sequence[Media]]:
        requested_fragment_ids = tuple(dict.fromkeys(fragment_ids))
        requested_fragment_id_set = set(requested_fragment_ids)
        media_by_fragment: Dict[MuseumNumber, List[Media]] = {
            fragment_id: [] for fragment_id in requested_fragment_ids
        }
        for stored_media in self._media.values():
            for association in stored_media.media.associations:
                if association.fragment_id in requested_fragment_id_set:
                    media_by_fragment[association.fragment_id].append(
                        stored_media.media
                    )
        return {
            fragment_id: fragment_media_in_order(fragment_id, media)
            for fragment_id, media in media_by_fragment.items()
        }

    def find_in_fragment(
        self, media_id: MediaId, fragment_id: MuseumNumber
    ) -> Optional[Media]:
        stored_media = self.find_stored_in_fragment(media_id, fragment_id)
        return stored_media.media if stored_media is not None else None

    def find_stored_in_fragment(
        self, media_id: MediaId, fragment_id: MuseumNumber
    ) -> Optional[StoredMedia]:
        stored_media = self.find_stored_by_id(media_id)
        if stored_media is None or not stored_media.media.is_associated_with(
            fragment_id
        ):
            return None
        return stored_media

    def find_primary_media(self, fragment_id: MuseumNumber) -> Optional[Media]:
        return primary_media_for(fragment_id, self.find_by_fragment(fragment_id))

    def find_primary_photo(self, fragment_id: MuseumNumber) -> Optional[Media]:
        return primary_photo_for(fragment_id, self.find_by_fragment(fragment_id))

    def set_primary(
        self, fragment_id: MuseumNumber, media_id: MediaId
    ) -> Sequence[Media]:
        if self.find_stored_in_fragment(media_id, fragment_id) is None:
            raise MediaNotFoundError(media_id)
        replacements = tuple(
            attr.evolve(
                item,
                media=with_primary(item.media, fragment_id, item.media.id == media_id),
            )
            for item in self._media.values()
            if item.media.is_associated_with(fragment_id)
        )
        self.replace_many(replacements)
        return self.find_by_fragment(fragment_id)

    def create(self, media: StoredMedia) -> MediaId:
        duplicate_source = (
            media.media.import_source is not None
            and self.find_by_import_source(media.media.import_source) is not None
        )
        if (
            media.media.id in self._media
            or media.media.id in self._deleting
            or duplicate_source
        ):
            raise MediaAlreadyExistsError(media.media.id)
        self._media[media.media.id] = media
        return media.media.id

    def replace(self, media: StoredMedia) -> StoredMedia:
        return self.replace_many((media,))[0]

    def replace_many(self, media: Sequence[StoredMedia]) -> Sequence[StoredMedia]:
        media_ids = [item.media.id for item in media]
        if len(media_ids) != len(set(media_ids)):
            raise ValueError("Cannot replace the same media twice in one batch.")
        for media_id in media_ids:
            if media_id not in self._media:
                raise MediaNotFoundError(media_id)
        require_unique_import_sources(self._media, media)
        if self.fail_next_replace:
            self.fail_next_replace = False
            raise RuntimeError("Metadata replacement failed.")

        previous = tuple(self._media[media_id] for media_id in media_ids)
        for item in media:
            self._media[item.media.id] = item
        return previous

    def delete(self, media_id: MediaId) -> Optional[StoredMedia]:
        self.call_log.append("repository.delete")
        deleted = self._media.pop(media_id, None)
        if deleted is not None:
            self._deleting[media_id] = deleted
        return self._deleting.get(media_id)

    def finish_delete(self, media: StoredMedia) -> None:
        self.call_log.append("repository.finish_delete")
        if self._deleting.get(media.media.id) == media:
            self._deleting.pop(media.media.id)
