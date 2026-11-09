"""Transactional contribution writes sharing media/source ownership and write lock."""

import uuid

from pymongo.errors import DuplicateKeyError

from ebl.changelog import create_entry
from ebl.media.application.media_errors import MediaNotFoundError
from ebl.media.application.media_management import MediaConflictError, now
from ebl.media.infrastructure.media_documents import load_stored, handle_document
from ebl.media.infrastructure.mongo_media_repository import MongoMediaRepository
from ebl.media.infrastructure.mongo_media_sources import reserve_sources
from ebl.media.infrastructure.mongo_media_mutations import MongoMediaMutation


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

    def commit_upload(self, command):
        request_id, fingerprint, lease = (
            command.request_id,
            command.fingerprint,
            command.lease,
        )
        stored, actor, number = command.stored, command.actor, command.fragment_id

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

    def mutate_media(self, command):
        def mutate(session):
            document = self._collection.find_one(
                {
                    "_id": str(command.media_id),
                    "state": "active",
                    "associations.fragmentId": str(command.fragment_id),
                },
                session=session,
            )
            if document is None:
                raise MediaNotFoundError(command.media_id)
            changed = MongoMediaMutation(self, command, session).apply(
                load_stored(document)
            )
            self._audit(
                session, command.actor, command.operation, changed, command.fragment_id
            )
            return changed

        return self._transaction(mutate)
