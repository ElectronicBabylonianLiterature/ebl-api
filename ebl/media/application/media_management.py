"""Contribution policy and orchestration over the established media stores."""

import hashlib
import json
import uuid
from typing import Callable

from ebl.errors import DataError
from ebl.media.domain import Media, MediaAssociation, MediaId, MediaType
from ebl.media.domain.publication import MediaSubmission
from ebl.media.application.media_stored import StoredMedia
from ebl.media.application.media_metadata_text import validate_review_metadata
from ebl.media.application.media_metadata import (
    RIGHTS_FIELDS,
    validate_metadata as validate_metadata,
)
from ebl.media.application.media_management_support import (
    MediaConflictError as MediaConflictError,
    MediaPermissionError as MediaPermissionError,
    MediaRevisionConflictError as MediaRevisionConflictError,
    MediaRevisionRequiredError as MediaRevisionRequiredError,
    now as now,
)
from ebl.media.application.media_management_policy import (
    apply_metadata,
    visible_to,
    editable_by,
    review_media,
)
from ebl.media.application.media_management_requests import (
    MediaUploadRequest,
    MediaMutationRequest,
    MediaUploadCommit,
    StoredMediaMutation,
)


# Reviews must name the exact revision the manager saw, so that an uploader's
# concurrent edit can never be published or rejected unseen.
REVISION_REQUIRED_OPERATIONS = frozenset({"publish", "reject"})


class MediaManagementService:
    def __init__(self, repository, store, prepare: Callable, limits) -> None:
        self.repository = repository
        self.store = store
        self._prepare = prepare
        self._limits = limits

    def list(self, number, actor, manager, contributor):
        return tuple(
            media
            for media in self.repository.find_by_fragment(number)
            if visible_to(media, actor, manager, contributor)
        )

    def get_stored(self, number, identifier, actor, manager, contributor):
        stored = self.repository.find_stored_in_fragment(identifier, number)
        return (
            stored
            if stored and visible_to(stored.media, actor, manager, contributor)
            else None
        )

    def upload(self, request: MediaUploadRequest):
        number, actor, key = request.fragment_id, request.actor, request.idempotency_key
        metadata, content = request.metadata, request.content
        length, mime = request.length, request.mime_type
        metadata = validate_metadata(metadata, upload=True)
        try:
            if str(uuid.UUID(key)) != key:
                raise ValueError()
        except (ValueError, TypeError, AttributeError) as error:
            raise DataError("A canonical UUID Idempotency-Key is required.") from error
        with self._prepare(
            content, content_length=length, declared_mime_type=mime, limits=self._limits
        ) as prepared:
            fingerprint = hashlib.sha256(
                json.dumps(
                    {
                        "metadata": metadata,
                        "checksum": prepared.original.representation.checksum.value,
                        "mime": prepared.original.representation.mime_type,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode()
            ).hexdigest()
            request_id = hashlib.sha256(
                json.dumps([actor, str(number), key]).encode()
            ).hexdigest()
            media_id = MediaId(
                str(uuid.uuid5(uuid.NAMESPACE_URL, "ebl:upload:" + request_id))
            )
            lease, existing = self.repository.begin_upload(
                request_id, fingerprint, media_id
            )
            if existing is not None:
                return existing.media, False
            try:
                handles = prepared.store(
                    self.store,
                    media_id,
                    on_staged=lambda handle: self.repository.stage_handle(
                        request_id, lease, handle
                    ),
                )
                media = Media(
                    id=media_id,
                    type=MediaType(metadata["type"]),
                    original_filename=metadata["originalFilename"],
                    associations=(MediaAssociation(number, 2147483647),),
                    representations=prepared.representations,
                    submission=MediaSubmission(
                        uploader_id=actor,
                        uploaded_at=now(),
                        rights_statement=metadata["rightsStatement"],
                        permission_attested=True,
                    ),
                )
                media = apply_metadata(
                    media,
                    {
                        key: value
                        for key, value in metadata.items()
                        if key != "originalFilename"
                    },
                )
                self.repository.commit_upload(
                    MediaUploadCommit(
                        request_id,
                        fingerprint,
                        lease,
                        StoredMedia(media, handles),
                        actor,
                        number,
                    )
                )
                return media, True
            except BaseException:
                # An uncertain commit may already be durable. Never delete bytes here.
                # Exact owned orphan handles remain quarantined for offline reconciliation.
                self.repository.fail_upload(request_id, lease)
                raise

    def mutate(self, request: MediaMutationRequest):
        metadata = request.metadata
        if request.operation == "edit":
            metadata = validate_metadata(metadata)
            if not request.manager and set(metadata) & RIGHTS_FIELDS:
                raise MediaPermissionError(
                    "Contributors cannot change publication rights."
                )
        elif not request.manager:
            raise MediaPermissionError("Media management permission is required.")
        else:
            validate_review_metadata(metadata)

        def change(media):
            request.authorize_associations(media)
            if not editable_by(media, request.actor, request.manager):
                raise MediaPermissionError("This submission cannot be edited.")
            if (
                request.operation in REVISION_REQUIRED_OPERATIONS
                and request.expected_revision is None
            ):
                raise MediaRevisionRequiredError(
                    "Reviews require If-Match with the media revision that was reviewed."
                )
            if request.operation == "edit":
                return apply_metadata(media, metadata)
            if request.operation in {"publish", "reject"}:
                return review_media(media, request)
            return media

        return self.repository.mutate_media(
            StoredMediaMutation(
                request.fragment_id,
                request.media_id,
                request.actor,
                request.operation,
                change,
                request.expected_revision,
            )
        )
