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
