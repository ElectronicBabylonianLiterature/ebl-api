from typing import Optional, Sequence

import attr

from ebl.iiif.domain.canvas import Canvas
from ebl.iiif.domain.language_map import LanguageMap
from ebl.iiif.domain.resources import (
    Agent,
    ExternalResource,
    ImageResource,
    MetadataEntry,
    RequiredStatement,
)

PRESENTATION_CONTEXT = "http://iiif.io/api/presentation/3/context.json"
MANIFEST_TYPE = "Manifest"
INDIVIDUALS_BEHAVIOR = "individuals"
LEFT_TO_RIGHT = "left-to-right"


@attr.attrs(auto_attribs=True, frozen=True)
class Manifest:
    id: str
    label: LanguageMap
    items: Sequence[Canvas]
    summary: Optional[LanguageMap] = None
    metadata: Sequence[MetadataEntry] = ()
    required_statement: Optional[RequiredStatement] = None
    rights: Optional[str] = None
    provider: Sequence[Agent] = ()
    homepage: Sequence[ExternalResource] = ()
    see_also: Sequence[ExternalResource] = ()
    part_of: Sequence[ExternalResource] = ()
    thumbnail: Sequence[ImageResource] = ()
    behavior: Sequence[str] = (INDIVIDUALS_BEHAVIOR,)
    viewing_direction: str = LEFT_TO_RIGHT
    type: str = MANIFEST_TYPE
    context: str = PRESENTATION_CONTEXT
