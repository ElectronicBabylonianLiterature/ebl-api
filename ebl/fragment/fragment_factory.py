from ebl.bibliography.reference import Reference
from ebl.fragment.folios import Folio, Folios
from ebl.fragment.fragment import (Fragment, FragmentNumber, Measure,
                                   UncuratedReference)
from ebl.fragment.record import (Record, RecordEntry, RecordType)
from ebl.text.text import Text


def create_folios(data):
    return Folios(tuple(Folio(**folio) for folio in data))


def create_record(data):
    return Record(tuple(
        RecordEntry(
            entry['user'],
            RecordType(entry['type']),
            entry['date']
        )
        for entry in data
    ))


class FragmentFactory:
    def __init__(self, bibliography):
        self._bibliography = bibliography

    @staticmethod
    def create(data):
        return Fragment(
            FragmentNumber(data['_id']),
            data['accession'],
            data['cdliNumber'],
            data['bmIdNumber'],
            data['publication'],
            data['description'],
            data['collection'],
            data['script'],
            data['museum'],
            Measure(**data['width']),
            Measure(**data['length']),
            Measure(**data['thickness']),
            tuple(data['joins']),
            create_record(data['record']),
            create_folios(data['folios']),
            Text.from_dict(data['text']),
            data.get('signs'),
            data['notes'],
            tuple(Reference.from_dict(reference)
                  for reference in data['references']),
            tuple(
                UncuratedReference(
                    reference['document'],
                    tuple(reference['pages'])
                )
                for reference in data['uncuratedReferences']
            ) if 'uncuratedReferences' in data else None
        )

    def create_denormalized(self, data):
        return self.create({
            **data,
            'references': [
                {
                    **reference,
                    'document': self._bibliography.find(reference['id'])
                }
                for reference in data['references']
            ]
        })
