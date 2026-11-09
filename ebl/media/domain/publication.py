"""Explicit publication metadata for new contributions; absent on legacy imports."""

from enum import Enum
from typing import Optional

import attr
from ebl.media.domain.validation import not_blank, strict_bool


class PublicationStatus(Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    PUBLISHED = "PUBLISHED"
    REJECTED = "REJECTED"


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class MediaRights:
    """Manager annotations on legacy imagery without invented upload/review data."""

    creator: str = attr.ib(default="", validator=attr.validators.instance_of(str))
    source_institution: str = attr.ib(
        default="", validator=attr.validators.instance_of(str)
    )
    copyright_holder: str = attr.ib(
        default="", validator=attr.validators.instance_of(str)
    )
    rights_statement: str = attr.ib(
        default="", validator=attr.validators.instance_of(str)
    )
    description: str = attr.ib(default="", validator=attr.validators.instance_of(str))


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class MediaSubmission:
    uploader_id: str = attr.ib(validator=not_blank)
    uploaded_at: str = attr.ib(validator=not_blank)
    rights_statement: str = attr.ib(validator=not_blank)
    permission_attested: bool = attr.ib(validator=strict_bool)
    publication_status: PublicationStatus = attr.ib(
        default=PublicationStatus.PENDING_REVIEW,
        validator=attr.validators.instance_of(PublicationStatus),
    )
    creator: str = attr.ib(default="", validator=attr.validators.instance_of(str))
    source_institution: str = attr.ib(
        default="", validator=attr.validators.instance_of(str)
    )
    copyright_holder: str = attr.ib(
        default="", validator=attr.validators.instance_of(str)
    )
    description: str = attr.ib(default="", validator=attr.validators.instance_of(str))
    reviewer_id: Optional[str] = attr.ib(
        default=None, validator=attr.validators.optional(not_blank)
    )
    reviewed_at: Optional[str] = attr.ib(
        default=None, validator=attr.validators.optional(not_blank)
    )
    review_reason: Optional[str] = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(str)),
    )

    def __attrs_post_init__(self):
        if self.publication_status is not PublicationStatus.PENDING_REVIEW and (
            not self.reviewer_id or not self.reviewed_at
        ):
            raise ValueError("Reviewed media requires reviewer identity and timestamp.")
        if (
            self.publication_status is PublicationStatus.PUBLISHED
            and not self.permission_attested
        ):
            raise ValueError("Published contributions require permission attestation.")


def is_published(media) -> bool:
    return media.submission is None or (
        media.submission.publication_status is PublicationStatus.PUBLISHED
    )
