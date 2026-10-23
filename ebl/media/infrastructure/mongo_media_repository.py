import uuid
from typing import Callable, Optional, Sequence, TypeVar

import attr
from pymongo import ASCENDING, ReadPreference
from pymongo.client_session import ClientSession
from pymongo.errors import DuplicateKeyError
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern

from ebl.media.application.media_errors import (
    MediaAlreadyExistsError,
    MediaNotFoundError,
)
from ebl.media.application.media_repository import MediaRepository
from ebl.media.application.media_selection import fragment_media_in_order, with_primary
from ebl.media.application.media_stored import StoredMedia
from ebl.media.domain import Media, MediaId
from ebl.media.infrastructure.media_documents import (
    load_stored,
    source_key,
    stored_document,
)
from ebl.media.infrastructure.mongo_media_reader import MongoMediaReader
from ebl.media.infrastructure.mongo_media_sources import (
    SOURCE_COLLECTION,
    reserve_sources,
    verify_source_reservations,
)
from ebl.transliteration.domain.museum_number import MuseumNumber

Result = TypeVar("Result")


class MongoMediaRepository(MongoMediaReader, MediaRepository):
    def assert_writable_topology(self) -> None:
        topology = self._database.client.admin.command("hello")
        if not topology.get("setName") and topology.get("msg") != "isdbgrid":
            raise ValueError(
                "Media writes require a MongoDB replica set or sharded cluster."
            )

    def create_indexes(self) -> None:
        self.assert_writable_topology()
        verify_source_reservations(self._database)
        self._collection.create_index(
            "sourceKey",
            name="media_import_source",
        )
        self._collection.create_index(
            [("associations.fragmentId", ASCENDING), ("state", ASCENDING)],
            name="media_fragment_state",
        )
        self._database["mediaLocks"].update_one(
            {"_id": "writes"}, {"$setOnInsert": {"revision": 0}}, upsert=True
        )
        self._database[SOURCE_COLLECTION].create_index(
            "mediaId", name="media_source_owner"
        )

    def _transaction(self, operation: Callable[[ClientSession], Result]) -> Result:
        self.assert_writable_topology()

        def locked_operation(session: ClientSession) -> Result:
            result = self._database["mediaLocks"].update_one(
                {"_id": "writes"}, {"$inc": {"revision": 1}}, session=session
            )
            if result.matched_count != 1:
                raise ValueError("Media indexes must be initialized before writing.")
            return operation(session)

        with self._database.client.start_session() as session:
            return session.with_transaction(
                locked_operation,
                read_concern=ReadConcern("snapshot"),
                write_concern=WriteConcern("majority"),
                read_preference=ReadPreference.PRIMARY,
            )

    @staticmethod
    def _active_document(media: StoredMedia) -> dict:
        if media.deletion_token is not None:
            raise ValueError("A tombstoned media state cannot be written as active.")
        return stored_document(media)

    def create(self, media: StoredMedia) -> MediaId:
        document = self._active_document(media)

        def insert(session: ClientSession) -> None:
            self._collection.insert_one(document, session=session)
            reserve_sources(self._database, (media,), session)

        try:
            self._transaction(insert)
        except DuplicateKeyError as error:
            raise MediaAlreadyExistsError(media.media.id) from error
        return media.media.id

    def _replace(self, media: StoredMedia, session: ClientSession) -> StoredMedia:
        previous = self._collection.find_one_and_replace(
            {"_id": str(media.media.id), "state": "active"},
            self._active_document(media),
            session=session,
        )
        if previous is None:
            raise MediaNotFoundError(media.media.id)
        return load_stored(previous)

    def replace(self, media: StoredMedia) -> StoredMedia:
        return self.replace_many((media,))[0]

    def replace_many(self, media: Sequence[StoredMedia]) -> Sequence[StoredMedia]:
        identifiers = [item.media.id for item in media]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("Cannot replace the same media more than once.")
        sources = [
            source_key(item.media.import_source)
            for item in media
            if item.media.import_source is not None
        ]
        if len(set(sources)) != len(sources):
            raise MediaAlreadyExistsError(media[-1].media.id)
        if not media:
            return ()

        def replace_batch(session: ClientSession) -> Sequence[StoredMedia]:
            previous = tuple(self._replace(item, session) for item in media)
            reserve_sources(self._database, media, session)
            return previous

        return self._transaction(replace_batch)

    def set_primary(
        self, fragment_id: MuseumNumber, media_id: MediaId
    ) -> Sequence[Media]:
        def promote(session: ClientSession) -> Sequence[Media]:
            documents = self._collection.find(
                {"state": "active", "associations.fragmentId": str(fragment_id)},
                session=session,
            )
            stored = tuple(load_stored(document) for document in documents)
            if not any(item.media.id == media_id for item in stored):
                raise MediaNotFoundError(media_id)
            replacements = tuple(
                attr.evolve(
                    item,
                    media=with_primary(
                        item.media, fragment_id, item.media.id == media_id
                    ),
                )
                for item in stored
            )
            for replacement in replacements:
                self._replace(replacement, session)
            return fragment_media_in_order(
                fragment_id, tuple(item.media for item in replacements)
            )

        return self._transaction(promote)

    def delete(self, media_id: MediaId) -> Optional[StoredMedia]:
        def tombstone(session: ClientSession) -> Optional[StoredMedia]:
            document = self._collection.find_one(
                {"_id": str(media_id)}, session=session
            )
            if document is None:
                return None
            if document["state"] == "active":
                document.update(state="deleted", deletionToken=str(uuid.uuid4()))
                self._collection.replace_one(
                    {"_id": str(media_id)}, document, session=session
                )
            return load_stored(document)

        return self._transaction(tombstone)

    def finish_delete(self, media: StoredMedia) -> None:
        if media.deletion_token is None:
            return
        expected = stored_document(media)
        expected.update(state="deleted", deletionToken=media.deletion_token)

        def finish(session: ClientSession) -> None:
            result = self._collection.delete_one(expected, session=session)
            if result.deleted_count:
                self._database[SOURCE_COLLECTION].delete_many(
                    {"mediaId": str(media.media.id)}, session=session
                )

        self._transaction(finish)
