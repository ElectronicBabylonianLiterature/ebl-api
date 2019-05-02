from enum import Enum, auto
from typing import NewType, Optional, Tuple

import attr

from ebl.text.labels import LineNumberLabel

BibliographyId = NewType('BibliographyId', str)


class ReferenceType(Enum):
    EDITION = auto()
    DISCUSSION = auto()
    COPY = auto()
    PHOTO = auto()


@attr.s(auto_attribs=True, frozen=True)
class Reference:
    id: BibliographyId
    type: ReferenceType
    pages: str = ''
    notes: str = ''
    lines_cited: Tuple[LineNumberLabel, ...] = tuple()
    document: Optional[dict] = None

    def to_dict(self, include_document=False) -> dict:
        result = {
            'id': self.id,
            'type': self.type.name,
            'pages': self.pages,
            'notes': self.notes,
            'linesCited': [
                line_number.to_value()
                for line_number in self.lines_cited
            ]
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
                LineNumberLabel(line_number)
                for line_number
                in data['linesCited']
            ),
            data.get('document', None)
        )


REFERENCE_DTO_SCHEMA = {
    'type': 'object',
    'properties': {
        'id': {
            'type': 'string'
        },
        'type': {
            'type': 'string',
            'enum': [name for name, _
                     in ReferenceType.__members__.items()]
        },
        'pages': {
            'type': 'string'
        },
        'notes': {
            'type': 'string'
        },
        'linesCited': {
            'type': 'array',
            'items': {
                'type': 'string'
            }
        }
    },
    'required': [
        'id',
        'type',
        'pages',
        'notes',
        'linesCited'
    ]
}
