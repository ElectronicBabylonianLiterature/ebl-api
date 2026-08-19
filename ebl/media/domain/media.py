import uuid
from enum import Enum
from typing import Optional, Sequence, Union

import attr

from ebl.common.domain.project import ResearchProject
from ebl.media.domain.mime import is_supported_raster_mime_type, is_svg_mime_type
from ebl.media.domain.representations import MediaRepresentations
from ebl.media.domain.validation import (
    non_negative_int,
    not_blank,
    strict_bool,
    tuple_or_empty,
)
from ebl.transliteration.domain.museum_number import MuseumNumber


def _museum_number_of(value: str | MuseumNumber) -> MuseumNumber:
    return value if isinstance(value, MuseumNumber) else MuseumNumber.of(value)


def _media_id_of(value: Union[str, "MediaId"]) -> "MediaId":
    return value if isinstance(value, MediaId) else MediaId(value)


def _associations_of(
    value: Optional[Sequence["MediaAssociation"]],
) -> tuple["MediaAssociation", ...]:
    return tuple_or_empty(value)


def _projects_of(
    value: Optional[Sequence[ResearchProject]],
) -> tuple[ResearchProject, ...]:
    return tuple_or_empty(value)


def _references_of(
    value: Optional[Sequence["MediaReference"]],
) -> tuple["MediaReference", ...]:
    return tuple_or_empty(value)


def _validate_associations(
    _instance: object, attribute: attr.Attribute, value: Sequence["MediaAssociation"]
) -> None:
    if not value:
        raise ValueError(f"Attribute {attribute.name} must contain at least one item.")

    fragment_ids = [association.fragment_id for association in value]
    if len(fragment_ids) != len(set(fragment_ids)):
        raise ValueError("Media cannot contain duplicate fragment associations.")


def _validate_mime_policy(
    media: "Media", _attribute: attr.Attribute, value: MediaRepresentations
) -> None:
    original_is_raster = is_supported_raster_mime_type(value.original.mime_type)
    original_is_svg = is_svg_mime_type(value.original.mime_type)
    preview_mime_types = []
    if value.display is not None:
        preview_mime_types.append(value.display.mime_type)
    preview_mime_types.extend(
        representation.mime_type for _, representation in value.thumbnails
    )
    valid_original = (
        original_is_raster
        if media.type is MediaType.PHOTO
        else original_is_raster or original_is_svg
    )
    valid_previews = all(
        is_supported_raster_mime_type(mime_type) for mime_type in preview_mime_types
    )
    if not valid_original or not valid_previews:
        raise ValueError(
            "Media representation MIME types are invalid. "
            "SVG representations are only valid as COPY originals."
        )


class MediaType(Enum):
    PHOTO = "PHOTO"
    COPY = "COPY"


@attr.s(auto_attribs=True, frozen=True, str=False)
class MediaId:
    """Canonical UUID media identity: one media item, one public spelling."""

    value: str = attr.ib(validator=not_blank)

    def __attrs_post_init__(self) -> None:
        try:
            parsed = uuid.UUID(self.value)
        except (ValueError, AttributeError, TypeError) as error:
            raise ValueError(f"'{self.value}' is not a valid UUID.") from error

        if str(parsed) != self.value:
            raise ValueError(
                f"'{self.value}' is not a canonical lowercase hyphenated UUID."
            )

    @classmethod
    def create(cls) -> "MediaId":
        return cls(str(uuid.uuid4()))

    def __str__(self) -> str:
        return self.value


@attr.s(auto_attribs=True, frozen=True)
class MediaAssociation:
    fragment_id: MuseumNumber = attr.ib(converter=_museum_number_of)
    sort_order: int = attr.ib(validator=non_negative_int)
    is_primary: bool = attr.ib(default=False, validator=strict_bool)


@attr.s(auto_attribs=True, frozen=True)
class MediaReference:
    bibliography_id: str = attr.ib(validator=not_blank)


@attr.s(auto_attribs=True, frozen=True)
class MediaImportSource:
    """Provenance of an imported original.

    `container` names the provider-side grouping (a GridFS bucket, an object
    store bucket) and is omitted for sources that have no such grouping.
    """

    system: str = attr.ib(validator=not_blank)
    file_id: str = attr.ib(validator=not_blank)
    container: Optional[str] = attr.ib(
        default=None, kw_only=True, validator=attr.validators.optional(not_blank)
    )


@attr.s(auto_attribs=True, frozen=True)
class Media:
    id: MediaId = attr.ib(converter=_media_id_of)
    type: MediaType = attr.ib(validator=attr.validators.instance_of(MediaType))
    original_filename: str = attr.ib(validator=not_blank)
    representations: MediaRepresentations = attr.ib(validator=_validate_mime_policy)
    associations: Sequence[MediaAssociation] = attr.ib(
        factory=tuple, converter=_associations_of, validator=_validate_associations
    )
    projects: Sequence[ResearchProject] = attr.ib(factory=tuple, converter=_projects_of)
    references: Sequence[MediaReference] = attr.ib(
        factory=tuple, converter=_references_of
    )
    caption: Optional[str] = None
    attribution: Optional[str] = None
    import_source: Optional[MediaImportSource] = None

    def __attrs_post_init__(self) -> None:
        object.__setattr__(
            self,
            "associations",
            tuple(
                sorted(
                    self.associations,
                    key=lambda association: (
                        association.sort_order,
                        str(association.fragment_id),
                    ),
                )
            ),
        )

    def association_for(self, fragment_id: str | MuseumNumber) -> MediaAssociation:
        normalized_fragment_id = _museum_number_of(fragment_id)
        try:
            return next(
                association
                for association in self.associations
                if association.fragment_id == normalized_fragment_id
            )
        except StopIteration as error:
            raise ValueError(
                f"Media {self.id} is not associated with fragment {fragment_id}."
            ) from error

    def is_associated_with(self, fragment_id: str | MuseumNumber) -> bool:
        try:
            self.association_for(fragment_id)
            return True
        except ValueError:
            return False
