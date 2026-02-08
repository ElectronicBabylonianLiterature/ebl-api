from enum import Enum, auto
from typing import NewType, Optional, Sequence

import attr

BibliographyId = NewType("BibliographyId", str)


class ReferenceType(Enum):
    EDITION = auto()
    DISCUSSION = auto()
    COPY = auto()
    PHOTO = auto()
    TRANSLATION = auto()
    ARCHAEOLOGY = auto()
    ACQUISITION = auto()
    SEAL = auto()


@attr.s(auto_attribs=True, frozen=True)
class Reference:
    id: BibliographyId
    type: ReferenceType
    pages: str = ""
    notes: str = ""
    lines_cited: Sequence[str] = ()
    document: Optional[dict] = None

    def set_document(self, new_document: dict) -> "Reference":
        return attr.evolve(self, document=new_document)
