import collections
from enum import Enum, auto
from typing import NewType, Tuple
import attr
from ebl.text.line import LineNumber


BibliographyId = NewType('BibliographyId', str)
PageRange = collections.namedtuple('PageRange', 'start end')


class ReferenceType(Enum):
    EDITION = auto()
    DISCUSSION = auto()
    COPY = auto()
    PHOTO = auto()


@attr.s(auto_attribs=True, frozen=True)
class Reference():
    id: BibliographyId
    type: ReferenceType
    pages: str = ''
    notes: str = ''
    lines_cited: Tuple[LineNumber, ...] = tuple()

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'type': self.type,
            'pages': self.pages,
            'notes': self.notes,
            'lines_cited': [line_number for line_number in self.lines_cited]
        }

    @staticmethod
    def from_dict(data: dict) -> 'Reference':
        return Reference(
            BibliographyId(data['id']),
            ReferenceType(data['type']),
            data['pages'],
            data['notes'],
            tuple(
                LineNumber(line_number)
                for line_number
                in data['lines_cited']
            )
        )
