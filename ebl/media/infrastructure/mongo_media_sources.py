from typing import Sequence

from pymongo.client_session import ClientSession
from pymongo.database import Database

from ebl.media.application.media_errors import MediaAlreadyExistsError
from ebl.media.application.media_stored import StoredMedia
from ebl.media.infrastructure.media_documents import source_key

SOURCE_COLLECTION = "mediaSources"


def reserve_sources(
    database: Database, replacements: Sequence[StoredMedia], session: ClientSession
) -> None:
    owners = {str(item.media.id) for item in replacements}
    sources = {
        source_key(item.media.import_source): item.media.id
        for item in replacements
        if item.media.import_source is not None
    }
    collection = database[SOURCE_COLLECTION]
    for source, media_id in sources.items():
        reservation = collection.find_one({"_id": source}, session=session)
        if reservation is not None and reservation["mediaId"] not in owners:
            raise MediaAlreadyExistsError(media_id)
    for source, media_id in sources.items():
        collection.update_one(
            {"_id": source},
            {"$set": {"mediaId": str(media_id)}},
            upsert=True,
            session=session,
        )
    collection.delete_many(
        {"mediaId": {"$in": list(owners)}, "_id": {"$nin": list(sources)}},
        session=session,
    )


def verify_source_reservations(database: Database) -> None:
    actual = {
        document["_id"]: document["mediaId"]
        for document in database[SOURCE_COLLECTION].find({})
    }
    expected: dict[str, str] = {}
    for document in database["media"].find({"sourceKey": {"$exists": True}}):
        source = document["sourceKey"]
        if source in expected:
            raise ValueError("Media contains duplicate import sources.")
        expected[source] = document["_id"]
    if actual != expected:
        raise ValueError(
            "Media source reservations require reconciliation before index setup."
        )
