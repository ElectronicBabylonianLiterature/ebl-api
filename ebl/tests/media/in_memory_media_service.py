from typing import Mapping, Optional, Sequence

from ebl.media.application import (
    MediaNotFoundError,
    MediaRepository,
    MediaRepresentationStore,
    MediaService,
    StoredMedia,
)
from ebl.media.domain import Media, MediaId
from ebl.tests.media.in_memory_media import InMemoryRepresentationStore
from ebl.transliteration.domain.museum_number import MuseumNumber


class InMemoryMediaService(MediaService):
    def __init__(
        self,
        repository: MediaRepository,
        representation_store: Optional[MediaRepresentationStore] = None,
    ) -> None:
        self._repository = repository
        self._representation_store = (
            representation_store or InMemoryRepresentationStore()
        )

    def list_fragment_media(self, fragment_id: MuseumNumber) -> Sequence[Media]:
        return self._repository.find_by_fragment(fragment_id)

    def find_media_by_fragments(
        self, fragment_ids: Sequence[MuseumNumber]
    ) -> Mapping[MuseumNumber, Sequence[Media]]:
        return self._repository.find_by_fragments(fragment_ids)

    def get_fragment_media(
        self, fragment_id: MuseumNumber, media_id: MediaId
    ) -> Optional[Media]:
        return self._repository.find_in_fragment(media_id, fragment_id)

    def get_stored_fragment_media(
        self, fragment_id: MuseumNumber, media_id: MediaId
    ) -> Optional[StoredMedia]:
        return self._repository.find_stored_in_fragment(media_id, fragment_id)

    def set_primary_media(
        self, fragment_id: MuseumNumber, media_id: MediaId
    ) -> Sequence[Media]:
        return self._repository.set_primary(fragment_id, media_id)

    def delete_media(self, media_id: MediaId) -> None:
        deleted = self._repository.delete(media_id)
        if deleted is None:
            raise MediaNotFoundError(media_id)
        for handle in deleted.representations.handles:
            self._representation_store.delete_representation(handle)
        self._repository.finish_delete(deleted)
