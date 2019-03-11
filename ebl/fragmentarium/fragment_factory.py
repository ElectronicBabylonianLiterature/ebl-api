from ebl.fragmentarium.fragment import (
    Fragment,
    RecordType,
    RecordEntry,
    Record,
    Folio,
    Folios,
    Measure,
    UncuratedReference
)
from ebl.bibliography.reference import Reference
from ebl.text.text import Text


class FragmentFactory:
    def __init__(self, bibliography):
        self._bibliography = bibliography

    @staticmethod
    def create(data):
        return Fragment(
            data['_id'],
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
            Record(tuple(
                RecordEntry(
                    entry['user'],
                    RecordType(entry['type']),
                    entry['date']
                )
                for entry in data['record']
            )),
            Folios(tuple(Folio(**folio) for folio in data['folios'])),
            Text.from_dict(data['text']),
            data.get('signs'),
            data['notes'],
            data.get('hits'),
            data.get('matching_lines'),
            tuple(Reference.from_dict(reference)
                  for reference in data['references']),
            tuple(
                UncuratedReference(
                    reference['document'],
                    tuple(reference['pages'])
                )
                for reference in data['uncurated_references']
            ) if 'uncurated_references' in data else None
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
