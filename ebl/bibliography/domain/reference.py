from enum import Enum, auto
from typing import NewType, Optional, Sequence

import attr

BibliographyId = NewType("BibliographyId", str)


class ReferenceType(Enum):
    EDITION = auto()
    DISCUSSION = auto()
    COPY = auto()
    PHOTO = auto()


@attr.s(auto_attribs=True, frozen=True)
class Reference:
    id: BibliographyId
    type: ReferenceType
    pages: str = ""
    notes: str = ""
    lines_cited: Sequence[str] = tuple()
    document: Optional[dict] = None


REFERENCE_DTO_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "type": {
            "type": "string",
            "enum": [name for name, _ in ReferenceType.__members__.items()],
        },
        "pages": {"type": "string"},
        "notes": {"type": "string"},
        "linesCited": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["id", "type", "pages", "notes", "linesCited"],
}
