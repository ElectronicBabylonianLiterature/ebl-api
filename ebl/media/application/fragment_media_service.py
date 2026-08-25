from typing import Mapping, Optional, Sequence

import attr

from ebl.media.application.media_errors import MediaNotFoundError
from ebl.media.application.media_repository import MediaRepository
from ebl.media.application.media_service import MediaService
from ebl.media.application.media_store import MediaRepresentationStore
from ebl.media.application.media_stored import StoredMedia
from ebl.media.domain import Media, MediaAssociation, MediaId
from ebl.transliteration.domain.museum_number import MuseumNumber


def _with_primary(media: Media, fragment_id: MuseumNumber, is_primary: bool) -> Media:
    return attr.evolve(
        media,
        associations=tuple(
            _evolved_association(association, is_primary)
            if association.fragment_id == fragment_id
            else association
            for association in media.associations
        ),
    )


def _evolved_association(
    association: MediaAssociation, is_primary: bool
) -> MediaAssociation:
    return attr.evolve(association, is_primary=is_primary)


class FragmentMediaService(MediaService):
    def __init__(
        self,
        repository: MediaRepository,
        representation_store: MediaRepresentationStore,
    ) -> None:
        self._repository = repository
        self._representation_store = representation_store

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
        if self._repository.find_in_fragment(media_id, fragment_id) is None:
            raise MediaNotFoundError(media_id)
        self._repository.replace_many(
            tuple(
                attr.evolve(
                    stored_media,
                    media=_with_primary(
                        stored_media.media, fragment_id, item.id == media_id
                    ),
                )
                for item, stored_media in self._stored_fragment_media(fragment_id)
            )
        )
        return self._repository.find_by_fragment(fragment_id)

    def delete_media(self, media_id: MediaId) -> None:
        if self._repository.find_by_id(media_id) is None:
            raise MediaNotFoundError(media_id)
        self._repository.delete(media_id)
        self._representation_store.delete_representations(media_id)

    def _stored_fragment_media(
        self, fragment_id: MuseumNumber
    ) -> Sequence[tuple[Media, StoredMedia]]:
        found = (
            (item, self._repository.find_stored_by_id(item.id))
            for item in self._repository.find_by_fragment(fragment_id)
        )
        return tuple(
            (item, stored_media)
            for item, stored_media in found
            if stored_media is not None
        )
