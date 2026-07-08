import re
import uuid
from enum import Enum
from typing import Optional, Sequence

import attr

from ebl.common.domain.project import ResearchProject
from ebl.transliteration.domain.museum_number import MuseumNumber


SHA256 = "sha256"
SVG_MIME_TYPE = "image/svg+xml"


def _not_empty(_, attribute: attr.Attribute, value: str) -> None:
    if not value:
        raise ValueError(f"Attribute {attribute.name} cannot be empty.")


def _positive(_, attribute: attr.Attribute, value: int) -> None:
    if value <= 0:
        raise ValueError(f"Attribute {attribute.name} must be positive.")


def _non_negative(_, attribute: attr.Attribute, value: int) -> None:
    if value < 0:
        raise ValueError(f"Attribute {attribute.name} cannot be negative.")


def _tuple_of(value):
    return tuple(value or ())


def _museum_number_of(value) -> MuseumNumber:
    return value if isinstance(value, MuseumNumber) else MuseumNumber.of(value)


def _media_id_of(value) -> "MediaId":
    return value if isinstance(value, MediaId) else MediaId(value)


def _checksum_value_of(value: str) -> str:
    return value.lower()


def _checksum_algorithm_of(value: str) -> str:
    return value.lower()


def _validate_associations(
    _, attribute: attr.Attribute, value: Sequence["MediaAssociation"]
) -> None:
    if not value:
        raise ValueError(f"Attribute {attribute.name} must contain at least one item.")

    fragment_ids = [association.fragment_id for association in value]
    if len(fragment_ids) != len(set(fragment_ids)):
        raise ValueError("Media cannot contain duplicate fragment associations.")


def _validate_svg_copy(media: "Media", _, value: "MediaRepresentations") -> None:
    if value.original.mime_type == SVG_MIME_TYPE and media.type is not MediaType.COPY:
        raise ValueError("SVG originals are only valid for COPY media.")


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
    id: str = attr.ib(validator=_not_empty)


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
    mime_type: str = attr.ib(validator=_not_empty)
    width: int = attr.ib(validator=_positive)
    height: int = attr.ib(validator=_positive)
    file_size: int = attr.ib(validator=_positive)
    checksum: Optional[MediaChecksum] = None


@attr.s(auto_attribs=True, frozen=True)
class MediaRepresentations:
    original: MediaRepresentation = attr.ib()
    thumbnails: Sequence[tuple[ThumbnailSize, MediaRepresentation]] = attr.ib(
        factory=tuple, converter=_tuple_of
    )

    def __attrs_post_init__(self) -> None:
        if self.original is None:
            raise ValueError("Media must contain an original representation.")
        if self.original.checksum is None:
            raise ValueError("Original representation must contain a checksum.")

        sizes = [size for size, _ in self.thumbnails]
        if len(sizes) != len(set(sizes)):
            raise ValueError("Media cannot contain duplicate thumbnail sizes.")


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
    representations: MediaRepresentations = attr.ib(validator=_validate_svg_copy)
    associations: Sequence[MediaAssociation] = attr.ib(
        factory=tuple, converter=_tuple_of, validator=_validate_associations
    )
    projects: Sequence[ResearchProject] = attr.ib(factory=tuple, converter=_tuple_of)
    references: Sequence[MediaReference] = attr.ib(factory=tuple, converter=_tuple_of)
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

    def association_for(self, fragment_id) -> MediaAssociation:
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

    def is_associated_with(self, fragment_id) -> bool:
        try:
            self.association_for(fragment_id)
            return True
        except ValueError:
            return False
