from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from ebl.common.domain.project import ResearchProject

if TYPE_CHECKING:
    from ebl.media.domain import media as media_types


def tuple_of_thumbnail_representations(
    value: Sequence[tuple[media_types.ThumbnailSize, media_types.MediaRepresentation]]
    | None,
) -> tuple[tuple[media_types.ThumbnailSize, media_types.MediaRepresentation], ...]:
    return tuple(value or ())


def tuple_of_associations(
    value: Sequence[media_types.MediaAssociation] | None,
) -> tuple[media_types.MediaAssociation, ...]:
    return tuple(value or ())


def tuple_of_projects(
    value: Sequence[ResearchProject] | None,
) -> tuple[ResearchProject, ...]:
    return tuple(value or ())


def tuple_of_references(
    value: Sequence[media_types.MediaReference] | None,
) -> tuple[media_types.MediaReference, ...]:
    return tuple(value or ())
