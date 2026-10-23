from typing import Mapping, Optional, Sequence

from pymongo import ReadPreference
from pymongo.collection import Collection
from pymongo.database import Database

from ebl.media.application.media_repository import MediaReader
from ebl.media.application.media_selection import (
    fragment_media_in_order,
    primary_media_for,
    primary_photo_for,
)
from ebl.media.application.media_stored import StoredMedia
from ebl.media.domain import Media, MediaId, MediaImportSource
from ebl.media.infrastructure.media_documents import load_stored, source_key
from ebl.transliteration.domain.museum_number import MuseumNumber

MEDIA_COLLECTION = "media"


class MongoMediaReader(MediaReader):
    def __init__(self, database: Database) -> None:
        self._database = database.with_options(read_preference=ReadPreference.PRIMARY)
        self._collection: Collection = self._database[MEDIA_COLLECTION]

    def _find(self, query: dict) -> Optional[StoredMedia]:
        document = self._collection.find_one({**query, "state": "active"})
        return load_stored(document) if document is not None else None

    def find_by_id(self, media_id: MediaId) -> Optional[Media]:
        stored = self.find_stored_by_id(media_id)
        return stored.media if stored else None

    def find_stored_by_id(self, media_id: MediaId) -> Optional[StoredMedia]:
        return self._find({"_id": str(media_id)})

    def find_by_import_source(
        self, import_source: MediaImportSource
    ) -> Optional[Media]:
        stored = self._find({"sourceKey": source_key(import_source)})
        return stored.media if stored else None

    def find_by_fragment(self, fragment_id: MuseumNumber) -> Sequence[Media]:
        return self.find_by_fragments((fragment_id,))[fragment_id]

    def find_by_fragments(
        self, fragment_ids: Sequence[MuseumNumber]
    ) -> Mapping[MuseumNumber, Sequence[Media]]:
        grouped: dict[MuseumNumber, list[Media]] = {
            fragment_id: [] for fragment_id in fragment_ids
        }
        if not grouped:
            return grouped
        documents = self._collection.find(
            {
                "state": "active",
                "associations.fragmentId": {
                    "$in": [str(fragment_id) for fragment_id in grouped]
                },
            }
        )
        for document in documents:
            media = load_stored(document).media
            for association in media.associations:
                if association.fragment_id in grouped:
                    grouped[association.fragment_id].append(media)
        return {
            fragment_id: fragment_media_in_order(fragment_id, media)
            for fragment_id, media in grouped.items()
        }

    def find_in_fragment(
        self, media_id: MediaId, fragment_id: MuseumNumber
    ) -> Optional[Media]:
        stored = self.find_stored_in_fragment(media_id, fragment_id)
        return stored.media if stored else None

    def find_stored_in_fragment(
        self, media_id: MediaId, fragment_id: MuseumNumber
    ) -> Optional[StoredMedia]:
        return self._find(
            {"_id": str(media_id), "associations.fragmentId": str(fragment_id)}
        )

    def find_primary_media(self, fragment_id: MuseumNumber) -> Optional[Media]:
        return primary_media_for(fragment_id, self.find_by_fragment(fragment_id))

    def find_primary_photo(self, fragment_id: MuseumNumber) -> Optional[Media]:
        return primary_photo_for(fragment_id, self.find_by_fragment(fragment_id))
