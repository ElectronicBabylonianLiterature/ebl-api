"""Operations inside the existing media transaction and global write lock."""

import uuid

import attr

from ebl.media.application.media_management_support import (
    MediaConflictError,
    MediaRevisionConflictError,
    now,
)
from ebl.media.application.media_selection import with_primary
from ebl.media.domain.publication import is_published
from ebl.media.infrastructure.media_documents import handle_document, load_stored


class MongoMediaMutation:
    def __init__(self, repository, command, session):
        self.repository = repository
        self.command = command
        self.session = session

    def apply(self, stored):
        # `change` authorizes first, so a mismatch is only revealed to callers
        # allowed to act on the media. The comparison runs on the snapshot read
        # of this transaction, under the media write lock, so no write can
        # interleave between it and the save below.
        changed = self.command.change(stored.media)
        expected, current = self.command.expected_revision, stored.media.revision
        if expected is not None and expected != current:
            raise MediaRevisionConflictError(expected, current)
        changed = attr.evolve(changed, revision=current + 1)
        if self.command.operation == "primary":
            return self._primary(changed)
        if self.command.operation == "remove":
            self._remove(stored, changed)
            return changed
        return self._save(stored, changed)

    def _primary(self, changed):
        if not is_published(changed):
            raise MediaConflictError("Only published media may be selected as primary.")
        number, identifier = self.command.fragment_id, self.command.media_id
        peers = self.repository._collection.find(
            {"state": "active", "associations.fragmentId": str(number)},
            session=self.session,
        )
        for document in peers:
            peer = load_stored(document)
            selected = peer.media.id == identifier
            media = with_primary(peer.media, number, selected)
            # Only the target's revision advances; peers merely lose the flag.
            if selected:
                media = attr.evolve(media, revision=changed.revision)
            self.repository._replace(attr.evolve(peer, media=media), self.session)
        return with_primary(changed, number, True)

    def _remove(self, stored, changed):
        self._suppress_legacy(stored, changed)
        # Metadata-only removal preserves bytes for requests already streaming.
        self.repository._collection.update_one(
            {"_id": str(self.command.media_id), "state": "active"},
            {
                "$set": {
                    "state": "deleted",
                    "deletionToken": str(uuid.uuid4()),
                    "deletedAt": now(),
                    "deletedBy": self.command.actor,
                    "revision": changed.revision,
                }
            },
            session=self.session,
        )

    def _legacy_file(self, stored):
        source = stored.media.import_source
        if source is None or source.system != "gridfs" or source.container != "photos":
            return None
        original = stored.representations.original
        database = self.repository._database
        registration = database["mediaFiles"].find_one(
            {
                "_id": original.value,
                "handle": handle_document(original),
                "ownership": "borrowed",
                "bucket": "photos",
            },
            session=self.session,
        )
        if registration is None:
            return None
        return database["photos.files"].find_one(
            {"_id": registration["fileId"]}, session=self.session
        )

    def _suppress_legacy(self, stored, changed):
        legacy_file = self._legacy_file(stored)
        if legacy_file is None:
            return
        for association in changed.associations:
            if legacy_file.get("filename") != f"{association.fragment_id}.jpg":
                continue
            self.repository._database["mediaLegacyVisibility"].update_one(
                {"_id": str(association.fragment_id)},
                {
                    "$set": {
                        "suppressed": True,
                        "removedBy": self.command.actor,
                        "removedAt": now(),
                    }
                },
                upsert=True,
                session=self.session,
            )

    def _save(self, stored, changed):
        if not is_published(changed):
            for association in changed.associations:
                changed = with_primary(changed, association.fragment_id, False)
        self.repository._replace(attr.evolve(stored, media=changed), self.session)
        return changed
