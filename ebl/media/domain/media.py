import re
import uuid
from enum import Enum
from typing import Optional, Sequence, Union

import attr

from ebl.common.domain.project import ResearchProject
from ebl.media.domain.mime import (
    is_supported_raster_mime_type,
    is_svg_mime_type,
    normalize_mime_type,
)
from ebl.transliteration.domain.museum_number import MuseumNumber

SHA256 = "sha256"


def _not_empty(_instance: object, attribute: attr.Attribute, value: str) -> None:
    if not value:
        raise ValueError(f"Attribute {attribute.name} cannot be empty.")


def _positive(_instance: object, attribute: attr.Attribute, value: int) -> None:
    if value <= 0:
        raise ValueError(f"Attribute {attribute.name} must be positive.")


def _non_negative(_instance: object, attribute: attr.Attribute, value: int) -> None:
    if value < 0:
        raise ValueError(f"Attribute {attribute.name} cannot be negative.")


def _museum_number_of(value: str | MuseumNumber) -> MuseumNumber:
    return value if isinstance(value, MuseumNumber) else MuseumNumber.of(value)


def _media_id_of(value: Union[str, "MediaId"]) -> "MediaId":
    return value if isinstance(value, MediaId) else MediaId(value)


def _checksum_value_of(value: str) -> str:
    return value.lower()


def _checksum_algorithm_of(value: str) -> str:
    return value.lower()


def _tuple_of_thumbnail_representations(
    value: Optional[Sequence[tuple["ThumbnailSize", "MediaRepresentation"]]],
) -> tuple[tuple["ThumbnailSize", "MediaRepresentation"], ...]:
    return tuple(value or ())


def _tuple_of_associations(
    value: Optional[Sequence["MediaAssociation"]],
) -> tuple["MediaAssociation", ...]:
    return tuple(value or ())


def _tuple_of_projects(
    value: Optional[Sequence[ResearchProject]],
) -> tuple[ResearchProject, ...]:
    return tuple(value or ())


def _tuple_of_references(
    value: Optional[Sequence["MediaReference"]],
) -> tuple["MediaReference", ...]:
    return tuple(value or ())


def _validate_associations(
    _instance: object, attribute: attr.Attribute, value: Sequence["MediaAssociation"]
) -> None:
    if not value:
        raise ValueError(f"Attribute {attribute.name} must contain at least one item.")

    fragment_ids = [association.fragment_id for association in value]
    if len(fragment_ids) != len(set(fragment_ids)):
        raise ValueError("Media cannot contain duplicate fragment associations.")


def _validate_mime_policy(
    media: "Media", _attribute: attr.Attribute, value: "MediaRepresentations"
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


class ThumbnailSize(Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


@attr.s(auto_attribs=True, frozen=True, str=False)
class MediaId:
    value: str = attr.ib(validator=_not_empty)

    def __attrs_post_init__(self) -> None:
        try:
            parsed = uuid.UUID(self.value)
        except ValueError as error:
            raise ValueError(f"'{self.value}' is not a valid UUID.") from error

        object.__setattr__(self, "value", str(parsed))

    @classmethod
    def create(cls) -> "MediaId":
        return cls(str(uuid.uuid4()))

    def __str__(self) -> str:
        return self.value


@attr.s(auto_attribs=True, frozen=True)
class MediaAssociation:
    fragment_id: MuseumNumber = attr.ib(converter=_museum_number_of)
    sort_order: int = attr.ib(validator=_non_negative)
    is_primary: bool = False


@attr.s(auto_attribs=True, frozen=True)
class MediaReference:
    bibliography_id: str = attr.ib(validator=_not_empty)


@attr.s(auto_attribs=True, frozen=True)
class MediaChecksum:
    algorithm: str = attr.ib(
        default=SHA256, converter=_checksum_algorithm_of, validator=_not_empty
    )
    value: str = attr.ib(default="", converter=_checksum_value_of, validator=_not_empty)

    def __attrs_post_init__(self) -> None:
        if self.algorithm != SHA256:
            raise ValueError("Media checksum algorithm must be sha256.")
        if not re.fullmatch(r"[0-9a-f]{64}", self.value):
            raise ValueError("Media checksum value must be 64 hexadecimal characters.")


@attr.s(auto_attribs=True, frozen=True)
class MediaRepresentation:
    mime_type: str = attr.ib(converter=normalize_mime_type, validator=_not_empty)
    width: int = attr.ib(validator=_positive)
    height: int = attr.ib(validator=_positive)
    file_size: int = attr.ib(validator=_positive)
    checksum: Optional[MediaChecksum] = None


@attr.s(auto_attribs=True, frozen=True)
class MediaRepresentations:
    original: MediaRepresentation = attr.ib()
    thumbnails: Sequence[tuple[ThumbnailSize, MediaRepresentation]] = attr.ib(
        factory=tuple, converter=_tuple_of_thumbnail_representations
    )
    display: Optional[MediaRepresentation] = attr.ib(default=None, kw_only=True)

    def __attrs_post_init__(self) -> None:
        if self.original is None:
            raise ValueError("Media must contain an original representation.")
        if self.original.checksum is None:
            raise ValueError("Original representation must contain a checksum.")

        sizes = [size for size, _ in self.thumbnails]
        if len(sizes) != len(set(sizes)):
            raise ValueError("Media cannot contain duplicate thumbnail sizes.")

    @property
    def all_representations(self) -> Sequence[MediaRepresentation]:
        representations = [self.original]
        if self.display is not None:
            representations.append(self.display)
        representations.extend(representation for _, representation in self.thumbnails)
        return tuple(representations)


@attr.s(auto_attribs=True, frozen=True)
class MediaImportSource:
    system: str = attr.ib(validator=_not_empty)
    bucket: str = attr.ib(validator=_not_empty)
    file_id: str = attr.ib(validator=_not_empty)


@attr.s(auto_attribs=True, frozen=True)
class Media:
    id: MediaId = attr.ib(converter=_media_id_of)
    type: MediaType
    original_filename: str = attr.ib(validator=_not_empty)
    representations: MediaRepresentations = attr.ib(validator=_validate_mime_policy)
    associations: Sequence[MediaAssociation] = attr.ib(
        factory=tuple,
        converter=_tuple_of_associations,
        validator=_validate_associations,
    )
    projects: Sequence[ResearchProject] = attr.ib(
        factory=tuple, converter=_tuple_of_projects
    )
    references: Sequence[MediaReference] = attr.ib(
        factory=tuple, converter=_tuple_of_references
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
