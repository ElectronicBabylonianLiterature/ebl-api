"""Metadata and publication policy independent of HTTP and persistence."""

import attr
from ebl.common.domain.project import ResearchProject
from ebl.errors import DataError
from ebl.media.domain import Media, MediaReference, MediaType
from ebl.media.domain.publication import (
    MediaRights,
    PublicationStatus,
    is_published,
)
from ebl.media.application.media_management_support import now


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


def review_media(media: Media, request) -> Media:
    submission = media.submission
    if submission is None:
        raise DataError("Legacy published imagery does not require review.")
    if request.operation == "publish" and (
        not submission.permission_attested or not submission.rights_statement.strip()
    ):
        raise DataError(
            "Publication requires explicit permission and rights information."
        )
    reviewed = attr.evolve(
        submission,
        publication_status=PublicationStatus.PUBLISHED
        if request.operation == "publish"
        else PublicationStatus.REJECTED,
        reviewer_id=request.actor,
        reviewed_at=now(),
        review_reason=request.metadata.get("reason"),
    )
    return attr.evolve(media, submission=reviewed)
