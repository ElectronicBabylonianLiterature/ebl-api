"""Transactional contribution writes sharing media/source ownership and write lock."""

import uuid

import attr
from pymongo.errors import DuplicateKeyError

from ebl.changelog import create_entry
from ebl.media.application.media_errors import MediaNotFoundError
from ebl.media.application.media_management import MediaConflictError, now
from ebl.media.application.media_selection import with_primary
from ebl.media.domain.publication import is_published
from ebl.media.infrastructure.media_documents import load_stored, handle_document
from ebl.media.infrastructure.mongo_media_repository import MongoMediaRepository
from ebl.media.infrastructure.mongo_media_sources import reserve_sources


class MongoMediaManagementRepository(MongoMediaRepository):
    def _audit(self, session, actor, operation, media, number):
        self._database["changelog"].insert_one(
            create_entry(
                {"sub": actor},
                "media",
                str(media.id),
                [
                    (
                        "add",
                        "",
                        [
                            ("event", operation),
                            ("fragment", str(number)),
                            ("at", now()),
                        ],
                    )
                ],
            ),
            session=session,
        )

    def begin_upload(self, request_id, fingerprint, media_id):
        lease = str(uuid.uuid4())

        def begin(session):
            requests = self._database["mediaUploadRequests"]
            previous = requests.find_one({"_id": request_id}, session=session)
            if previous is not None:
                if previous["fingerprint"] != fingerprint:
                    raise MediaConflictError(
                        "Idempotency key was used for different content or metadata."
                    )
                if previous["state"] == "committed":
                    document = self._collection.find_one(
                        {"_id": previous["mediaId"], "state": "active"}, session=session
                    )
                    if document is None:
                        raise MediaConflictError(
                            "The previously submitted media was removed."
                        )
                    return None, load_stored(document)
                if previous["state"] == "staging":
                    raise MediaConflictError(
                        "This upload is already being processed. Retry later."
                    )
                requests.update_one(
                    {"_id": request_id},
                    {"$set": {"state": "staging", "lease": lease, "updatedAt": now()}},
                    session=session,
                )
            else:
                requests.insert_one(
                    {
                        "_id": request_id,
                        "fingerprint": fingerprint,
                        "mediaId": str(media_id),
                        "state": "staging",
                        "lease": lease,
                        "updatedAt": now(),
                    },
                    session=session,
                )
            return lease, None

        return self._transaction(begin)

    def commit_upload(self, request_id, fingerprint, lease, stored, actor, number):
        def commit(session):
            result = self._database["mediaUploadRequests"].update_one(
                {
                    "_id": request_id,
                    "fingerprint": fingerprint,
                    "lease": lease,
                    "state": "staging",
                },
                {"$set": {"state": "committed", "updatedAt": now()}},
                session=session,
            )
            if result.matched_count != 1:
                raise MediaConflictError("Upload reservation is no longer current.")
            self._collection.insert_one(self._active_document(stored), session=session)
            reserve_sources(self._database, (stored,), session)
            self._audit(session, actor, "upload-created", stored.media, number)

        try:
            self._transaction(commit)
        except DuplicateKeyError as error:
            raise MediaConflictError("Upload has already been committed.") from error

    def stage_handle(self, request_id, lease, handle):
        result = self._database["mediaUploadRequests"].update_one(
            {"_id": request_id, "lease": lease, "state": "staging"},
            {
                "$push": {"stagedHandles": handle_document(handle)},
                "$set": {"updatedAt": now()},
            },
        )
        if result.matched_count != 1:
            raise MediaConflictError("Upload reservation is no longer current.")

    def fail_upload(self, request_id, lease):
        self._database["mediaUploadRequests"].update_one(
            {"_id": request_id, "lease": lease, "state": "staging"},
            {"$set": {"state": "failed", "updatedAt": now()}},
        )

    def mutate_media(self, number, identifier, actor, operation, change):
        def mutate(session):
            document = self._collection.find_one(
                {
                    "_id": str(identifier),
                    "state": "active",
                    "associations.fragmentId": str(number),
                },
                session=session,
            )
            if document is None:
                raise MediaNotFoundError(identifier)
            stored = load_stored(document)
            changed = change(stored.media)
            if operation == "primary":
                if not is_published(changed):
                    raise MediaConflictError(
                        "Only published media may be selected as primary."
                    )
                peers = self._collection.find(
                    {"state": "active", "associations.fragmentId": str(number)},
                    session=session,
                )
                for peer_document in peers:
                    peer = load_stored(peer_document)
                    updated = attr.evolve(
                        peer,
                        media=with_primary(
                            peer.media, number, peer.media.id == identifier
                        ),
                    )
                    self._replace(updated, session)
                changed = with_primary(changed, number, True)
            elif operation == "remove":
                source = changed.import_source
                if (
                    source is not None
                    and source.system == "gridfs"
                    and source.container == "photos"
                ):
                    original = stored.representations.original
                    registration = self._database["mediaFiles"].find_one(
                        {
                            "_id": original.value,
                            "handle": handle_document(original),
                            "ownership": "borrowed",
                            "bucket": "photos",
                        },
                        session=session,
                    )
                    legacy_file = (
                        self._database["photos.files"].find_one(
                            {"_id": registration["fileId"]}, session=session
                        )
                        if registration is not None
                        else None
                    )
                    for association in changed.associations:
                        if (
                            legacy_file is not None
                            and legacy_file.get("filename")
                            == f"{association.fragment_id}.jpg"
                        ):
                            self._database["mediaLegacyVisibility"].update_one(
                                {"_id": str(association.fragment_id)},
                                {
                                    "$set": {
                                        "suppressed": True,
                                        "removedBy": actor,
                                        "removedAt": now(),
                                    }
                                },
                                upsert=True,
                                session=session,
                            )
                # HTTP only hides metadata. Never destroy bytes an active reader uses.
                self._collection.update_one(
                    {"_id": str(identifier), "state": "active"},
                    {
                        "$set": {
                            "state": "deleted",
                            "deletionToken": str(uuid.uuid4()),
                            "deletedAt": now(),
                            "deletedBy": actor,
                        }
                    },
                    session=session,
                )
            else:
                if not is_published(changed):
                    for association in changed.associations:
                        changed = with_primary(changed, association.fragment_id, False)
                self._replace(attr.evolve(stored, media=changed), session)
            self._audit(session, actor, operation, changed, number)
            return changed

        return self._transaction(mutate)
