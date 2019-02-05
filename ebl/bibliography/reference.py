from enum import Enum, auto
from typing import NewType, Tuple, Optional
import attr
from ebl.text.line import LineNumber


BibliographyId = NewType('BibliographyId', str)


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
    document: Optional[dict] = None

    def to_dict(self, include_document=False) -> dict:
        result = {
            'id': self.id,
            'type': self.type.name,
            'pages': self.pages,
            'notes': self.notes,
            'linesCited': [line_number for line_number in self.lines_cited]
        }
        return (
            {
                **result,
                'document': self.document
            }
            if include_document else
            result
        )

    @staticmethod
    def from_dict(data: dict) -> 'Reference':
        return Reference(
            BibliographyId(data['id']),
            ReferenceType[data['type']],
            data['pages'],
            data['notes'],
            tuple(
                LineNumber(line_number)
                for line_number
                in data['linesCited']
            ),
            data.get('document', None)
        )
