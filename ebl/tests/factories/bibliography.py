# pylint: disable=R0903
import factory.fuzzy

from ebl.bibliography.reference import BibliographyId, Reference, ReferenceType
from ebl.tests.factories.collections import TupleFactory


class ReferenceFactory(factory.Factory):
    class Meta:
        model = Reference

    id = factory.Sequence(lambda n: BibliographyId(f'RN.{n}'))
    type = factory.fuzzy.FuzzyChoice(ReferenceType)
    pages = factory.Sequence(lambda n: f'{n}-{n+2}, {n+5}')
    notes = factory.Faker('paragraph')
    lines_cited = factory.List([
        factory.Sequence(lambda n: f"r. iii*! {n}'.{n+1}a")
    ], TupleFactory)


class ReferenceWithDocumentFactory(ReferenceFactory):
    document = factory.Dict({
        "id": factory.SelfAttribute('..id'),
        "title": ("The Synergistic Activity of Thyroid Transcription Factor 1 "
                  "and Pax 8 Relies on the Promoter/Enhancer Interplay"),
        "type": "article-journal",
        "DOI": "10.1210/MEND.16.4.0808",
        "issued": {
            "date-parts": [
                [
                    2002,
                    1,
                    1
                ]
            ]
        },
        "PMID": "11923479",
        "volume": "16",
        "page": "837-846",
        "issue": "4",
        "container-title": "Molecular Endocrinology",
        "author": [
            {
                "given": "Stefania",
                "family": "Miccadei"
            },
            {
                "given": "Rossana",
                "family": "De Leo"
            },
            {
                "given": "Enrico",
                "family": "Zammarchi"
            },
            {
                "given": "Pier Giorgio",
                "family": "Natali"
            },
            {
                "given": "Donato",
                "family": "Civitareale"
            }
        ]
    })
