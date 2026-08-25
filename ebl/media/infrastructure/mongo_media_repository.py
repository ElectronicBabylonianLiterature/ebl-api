from typing import Any, Mapping, Optional, Sequence

import pymongo
from pymongo import ReplaceOne
from pymongo.database import Database

from ebl.errors import DuplicateError, NotFoundError
from ebl.media.application.media_errors import (
    MediaAlreadyExistsError,
    MediaNotFoundError,
)
from ebl.media.application.media_repository import MediaRepository
from ebl.media.application.media_selection import (
    fragment_media_in_order,
    primary_media_for,
    primary_photo_for,
)
from ebl.media.application.media_stored import StoredMedia
from ebl.media.domain import Media, MediaId, MediaImportSource, MediaType
from ebl.media.infrastructure.media_documents import (
    media_of,
    stored_media_document,
    stored_media_of,
)
from ebl.mongo_collection import MongoCollection
from ebl.transliteration.domain.museum_number import MuseumNumber

COLLECTION = "media"
FRAGMENT_ID = "associations.fragmentId"


def _import_source_query(import_source: MediaImportSource) -> dict[str, Any]:
    return {
        "importSource.system": import_source.system,
        "importSource.fileId": import_source.file_id,
        "importSource.container": import_source.container,
    }


class MongoMediaRepository(MediaRepository):
    def __init__(self, database: Database) -> None:
        self._collection = MongoCollection(database, COLLECTION)

    def create_indexes(self) -> None:
        self._collection.create_index([(FRAGMENT_ID, pymongo.ASCENDING)])
        self._collection.create_index(
            [(FRAGMENT_ID, pymongo.ASCENDING), ("type", pymongo.ASCENDING)]
        )
        self._collection.create_index(
            [("representations.original.checksum.value", pymongo.ASCENDING)]
        )
        self._collection.create_index(
            [
                ("importSource.system", pymongo.ASCENDING),
                ("importSource.fileId", pymongo.ASCENDING),
                ("importSource.container", pymongo.ASCENDING),
            ]
        )

    def find_by_id(self, media_id: MediaId) -> Optional[Media]:
        document = self._find_document({"_id": str(media_id)})
        return None if document is None else media_of(document)

    def find_stored_by_id(self, media_id: MediaId) -> Optional[StoredMedia]:
        document = self._find_document({"_id": str(media_id)})
        return None if document is None else stored_media_of(document)

    def find_by_fragment(self, fragment_id: MuseumNumber) -> Sequence[Media]:
        return fragment_media_in_order(
            fragment_id, self._find_media({FRAGMENT_ID: str(fragment_id)})
        )

    def find_by_fragments(
        self, fragment_ids: Sequence[MuseumNumber]
    ) -> Mapping[MuseumNumber, Sequence[Media]]:
        requested = tuple(dict.fromkeys(fragment_ids))
        if not requested:
            return {}
        media = self._find_media(
            {FRAGMENT_ID: {"$in": [str(fragment_id) for fragment_id in requested]}}
        )
        return {
            fragment_id: fragment_media_in_order(
                fragment_id,
                tuple(item for item in media if item.is_associated_with(fragment_id)),
            )
            for fragment_id in requested
        }

    def find_in_fragment(
        self, media_id: MediaId, fragment_id: MuseumNumber
    ) -> Optional[Media]:
        document = self._find_in_fragment_document(media_id, fragment_id)
        return None if document is None else media_of(document)

    def find_stored_in_fragment(
        self, media_id: MediaId, fragment_id: MuseumNumber
    ) -> Optional[StoredMedia]:
        document = self._find_in_fragment_document(media_id, fragment_id)
        return None if document is None else stored_media_of(document)

    def find_primary_media(self, fragment_id: MuseumNumber) -> Optional[Media]:
        return primary_media_for(fragment_id, self.find_by_fragment(fragment_id))

    def find_primary_photo(self, fragment_id: MuseumNumber) -> Optional[Media]:
        return primary_photo_for(
            fragment_id,
            fragment_media_in_order(
                fragment_id,
                self._find_media(
                    {FRAGMENT_ID: str(fragment_id), "type": MediaType.PHOTO.value}
                ),
            ),
        )

    def find_by_import_source(
        self, import_source: MediaImportSource
    ) -> Optional[Media]:
        document = self._find_document(_import_source_query(import_source))
        return None if document is None else media_of(document)

    def create(self, media: StoredMedia) -> MediaId:
        try:
            self._collection.insert_one(stored_media_document(media))
        except DuplicateError as error:
            raise MediaAlreadyExistsError(media.media.id) from error
        return media.media.id

    def replace(self, media: StoredMedia) -> StoredMedia:
        return self.replace_many((media,))[0]

    def replace_many(self, media: Sequence[StoredMedia]) -> Sequence[StoredMedia]:
        media_ids = [item.media.id for item in media]
        if len(media_ids) != len(set(media_ids)):
            raise ValueError("Cannot replace the same media twice in one batch.")
        if not media_ids:
            return ()
        previous = self._load_all(media_ids)
        self._collection.bulk_write(
            [
                ReplaceOne({"_id": str(item.media.id)}, stored_media_document(item))
                for item in media
            ]
        )
        return previous

    def delete(self, media_id: MediaId) -> None:
        try:
            self._collection.delete_one({"_id": str(media_id)})
        except NotFoundError:
            return

    def _load_all(self, media_ids: Sequence[MediaId]) -> Sequence[StoredMedia]:
        documents = {
            document["_id"]: document
            for document in self._collection.find_many(
                {"_id": {"$in": [str(media_id) for media_id in media_ids]}}
            )
        }
        for media_id in media_ids:
            if str(media_id) not in documents:
                raise MediaNotFoundError(media_id)
        return tuple(
            stored_media_of(documents[str(media_id)]) for media_id in media_ids
        )

    def _find_in_fragment_document(
        self, media_id: MediaId, fragment_id: MuseumNumber
    ) -> Optional[Mapping[str, Any]]:
        return self._find_document(
            {"_id": str(media_id), FRAGMENT_ID: str(fragment_id)}
        )

    def _find_document(self, query: Mapping[str, Any]) -> Optional[Mapping[str, Any]]:
        try:
            return self._collection.find_one(query)
        except NotFoundError:
            return None

    def _find_media(self, query: Mapping[str, Any]) -> Sequence[Media]:
        return tuple(
            media_of(document) for document in self._collection.find_many(query)
        )
