"""Contribution policy and orchestration over the established media stores."""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

import attr

from ebl.common.domain.project import ResearchProject
from ebl.errors import DataError
from ebl.media.domain import Media, MediaAssociation, MediaId, MediaReference, MediaType
from ebl.media.domain.publication import (
    MediaSubmission,
    MediaRights,
    PublicationStatus,
    is_published,
)
from ebl.media.application.media_stored import StoredMedia


class MediaConflictError(Exception):
    pass


class MediaPermissionError(Exception):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


TEXT_FIELDS = {
    "caption",
    "attribution",
    "creator",
    "sourceInstitution",
    "copyrightHolder",
    "rightsStatement",
    "description",
}
UPLOAD_FIELDS = TEXT_FIELDS | {
    "originalFilename",
    "type",
    "permissionAttested",
    "references",
    "projects",
}
RIGHTS_FIELDS = {"rightsStatement", "permissionAttested", "copyrightHolder"}


def validate_metadata(data: Any, *, upload: bool = False) -> dict:
    if not isinstance(data, dict) or set(data) - UPLOAD_FIELDS:
        raise DataError("Unknown or invalid media metadata fields.")
    if not upload and "originalFilename" in data:
        raise DataError("Original files cannot be replaced through metadata editing.")
    for field in TEXT_FIELDS | {"originalFilename"}:
        if field in data and (
            not isinstance(data[field], str) or len(data[field]) > 4000
        ):
            raise DataError(f"{field} must be text of at most 4000 characters.")
    if "type" in data and (
        not isinstance(data["type"], str) or data["type"] not in {"PHOTO", "COPY"}
    ):
        raise DataError("Image type must be PHOTO or COPY.")
    if "rightsStatement" in data and not data["rightsStatement"].strip():
        raise DataError("Rights statement must not be blank.")
    if "permissionAttested" in data and data["permissionAttested"] is not True:
        raise DataError("Permission attestation must be explicitly confirmed.")
    if "references" in data:
        references = data["references"]
        if (
            not isinstance(references, list)
            or len(references) > 100
            or any(
                not isinstance(item, dict)
                or set(item) != {"id"}
                or not isinstance(item["id"], str)
                or not item["id"].strip()
                or len(item["id"]) > 200
                for item in references
            )
        ):
            raise DataError("References must be a list of bibliography identifiers.")
    if "projects" in data:
        projects = data["projects"]
        if (
            not isinstance(projects, list)
            or len(projects) > len(ResearchProject)
            or any(
                not isinstance(project, str)
                or project not in ResearchProject.__members__
                for project in projects
            )
        ):
            raise DataError("Unknown research project.")
    if upload:
        for field in (
            "originalFilename",
            "type",
            "caption",
            "rightsStatement",
            "permissionAttested",
        ):
            if not data.get(field):
                raise DataError(f"{field} is required.")
        if not data["caption"].strip() or not data["rightsStatement"].strip():
            raise DataError("Caption and rights statement must not be blank.")
        name = data["originalFilename"]
        if (
            not name.strip()
            or len(name) > 255
            or any(character in name for character in ("/", "\\", "\x00", "\r", "\n"))
        ):
            raise DataError("Invalid original filename.")
    elif "caption" in data and not data["caption"].strip():
        raise DataError("Caption must not be blank.")
    return dict(data)


def visible_to(
    media: Media, actor: str | None, manager: bool, contributor: bool
) -> bool:
    return (
        is_published(media)
        or manager
        or bool(
            contributor and media.submission and media.submission.uploader_id == actor
        )
    )


def editable_by(media: Media, actor: str, manager: bool) -> bool:
    return manager or bool(
        media.submission
        and media.submission.uploader_id == actor
        and media.submission.publication_status is PublicationStatus.PENDING_REVIEW
    )


def apply_metadata(media: Media, metadata: dict) -> Media:
    changes = {
        key: metadata[key] for key in ("caption", "attribution") if key in metadata
    }
    if "type" in metadata:
        changes["type"] = MediaType(metadata["type"])
    if "references" in metadata:
        changes["references"] = tuple(
            MediaReference(item["id"]) for item in metadata["references"]
        )
    if "projects" in metadata:
        changes["projects"] = tuple(
            ResearchProject[name] for name in metadata["projects"]
        )
    submission_fields = {
        "creator": "creator",
        "sourceInstitution": "source_institution",
        "copyrightHolder": "copyright_holder",
        "rightsStatement": "rights_statement",
        "permissionAttested": "permission_attested",
        "description": "description",
    }
    submission_changes = {
        target: metadata[source]
        for source, target in submission_fields.items()
        if source in metadata
    }
    if submission_changes:
        if media.submission is None:
            if "permission_attested" in submission_changes:
                raise DataError(
                    "Legacy rights annotations cannot fabricate an upload permission attestation."
                )
            changes["rights"] = attr.evolve(
                media.rights or MediaRights(), **submission_changes
            )
        else:
            changes["submission"] = attr.evolve(media.submission, **submission_changes)
    try:
        return attr.evolve(media, **changes)
    except ValueError as error:
        raise DataError(
            "Metadata is incompatible with the stored media type."
        ) from error


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

    def upload(self, number, actor, key, metadata, content, length, mime):
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
                    request_id,
                    fingerprint,
                    lease,
                    StoredMedia(media, handles),
                    actor,
                    number,
                )
                return media, True
            except BaseException:
                # An uncertain commit may already be durable. Never delete bytes here.
                # Exact owned orphan handles remain quarantined for offline reconciliation.
                self.repository.fail_upload(request_id, lease)
                raise

    def mutate(
        self,
        number,
        identifier,
        actor,
        manager,
        operation,
        metadata,
        authorize_associations,
    ):
        if operation == "edit":
            metadata = validate_metadata(metadata)
            if not manager and set(metadata) & RIGHTS_FIELDS:
                raise MediaPermissionError(
                    "Contributors cannot change publication rights."
                )
        elif not manager:
            raise MediaPermissionError("Media management permission is required.")

        def change(media):
            authorize_associations(media)
            if not editable_by(media, actor, manager):
                raise MediaPermissionError("This submission cannot be edited.")
            if operation == "edit":
                return apply_metadata(media, metadata)
            if operation in {"publish", "reject"}:
                if media.submission is None:
                    raise DataError("Legacy published imagery does not require review.")
                if operation == "publish" and (
                    not media.submission.permission_attested
                    or not media.submission.rights_statement.strip()
                ):
                    raise DataError(
                        "Publication requires explicit permission and rights information."
                    )
                submission = attr.evolve(
                    media.submission,
                    publication_status=(
                        PublicationStatus.PUBLISHED
                        if operation == "publish"
                        else PublicationStatus.REJECTED
                    ),
                    reviewer_id=actor,
                    reviewed_at=now(),
                    review_reason=metadata.get("reason"),
                )
                return attr.evolve(media, submission=submission)
            return media

        return self.repository.mutate_media(
            number, identifier, actor, operation, change
        )
