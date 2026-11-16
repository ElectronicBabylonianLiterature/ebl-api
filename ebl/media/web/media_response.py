from typing import Sequence, cast

from ebl.media.domain import Media
from ebl.transliteration.domain.museum_number import MuseumNumber

from ebl.media.application.media_dtos import FragmentMediaResponseDto
from ebl.media.application.media_schemas import FragmentMediaResponseDtoSchema


def _shows_management_fields(item: Media, viewer: tuple[str, bool] | None) -> bool:
    if viewer is None or item.submission is None:
        return False
    actor, manager = viewer
    return manager or item.submission.uploader_id == actor


def _shows_revision(item: Media, viewer: tuple[str, bool] | None) -> bool:
    """Managers see every item's revision (legacy items included, since
    they may act on them); contributors only their own submissions'."""
    if viewer is None:
        return False
    actor, manager = viewer
    return manager or (
        item.submission is not None and item.submission.uploader_id == actor
    )


def media_response(
    number: MuseumNumber,
    media: Sequence[Media],
    *,
    viewer: tuple[str, bool] | None = None,
) -> dict[str, object]:
    """Serialize media; `viewer` is `(actor, is_manager)` for management views.

    Management-only fields are attached per item, only for managers or the
    item's own uploader. Other items are serialized like the public view.
    """
    result = cast(
        dict[str, object],
        FragmentMediaResponseDtoSchema().dump(
            FragmentMediaResponseDto.of(number, media)
        ),
    )
    resources = cast(list[dict[str, object]], result["media"])
    if len(resources) != len(media):
        raise ValueError("Media response item count does not match media.")
    for index, item in enumerate(media):
        resource = resources[index]
        if item.submission is not None:
            submission = item.submission
            resource.update(
                publicationStatus=submission.publication_status.value,
                creator=submission.creator,
                sourceInstitution=submission.source_institution,
                copyrightHolder=submission.copyright_holder,
                rightsStatement=submission.rights_statement,
            )
            if _shows_management_fields(item, viewer):
                resource.update(
                    originalFilename=item.original_filename,
                    uploaderId=submission.uploader_id,
                    uploadedAt=submission.uploaded_at,
                    permissionAttested=submission.permission_attested,
                    description=submission.description,
                    projects=[project.name for project in item.projects],
                    reviewerId=submission.reviewer_id,
                    reviewedAt=submission.reviewed_at,
                    reviewReason=submission.review_reason,
                )
        elif item.rights is not None:
            resource.update(
                rightsAnnotated=True,
                creator=item.rights.creator,
                sourceInstitution=item.rights.source_institution,
                copyrightHolder=item.rights.copyright_holder,
                rightsStatement=item.rights.rights_statement,
                description=item.rights.description,
            )
        if _shows_revision(item, viewer):
            resource["revision"] = item.revision
    return result
