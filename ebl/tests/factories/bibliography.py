import factory.fuzzy  # pyre-ignore

from ebl.bibliography.domain.reference import (
    BibliographyId,
    Reference,
    ReferenceType,
)
from ebl.tests.factories.collections import TupleFactory


class ReferenceFactory(factory.Factory):  # pyre-ignore[11]
    class Meta:
        model = Reference

    id = factory.Sequence(lambda n: BibliographyId(f"RN.{n}"))
    type = factory.fuzzy.FuzzyChoice(ReferenceType)
    pages = factory.Sequence(lambda n: f"{n}-{n+2}, {n+5}")
    notes = factory.Faker("paragraph")
    lines_cited = factory.List(
        [factory.Sequence(lambda n: f"r. iii*! {n}'.{n+1}a")], TupleFactory
    )


class BibliographyEntryFactory(factory.Factory):  # pyre-ignore
    class Meta:
        model = dict
        rename = {
            "container_title": "container-title",
            "container_title_short": "container-title-short",
            "collection_number": "collection-number",
        }

    id = "Q30000000"
    title = (
        "The Synergistic Activity of Thyroid Transcription Factor 1 "
        "and Pax 8 Relies on the Promoter/Enhancer Interplay"
    )
    type = "article-journal"
    DOI = "10.1210/MEND.16.4.0808"
    issued = {"date-parts": [[2002, 1, 1]]}
    PMID = "11923479"
    volume = "16"
    page = "837-846"
    issue = "4"
    container_title = "Molecular Endocrinology"
    container_title_short = "ME"
    collection_number = "1"
    author = [
        {"given": "Stefania", "family": "Miccadei"},
        {"given": "Rossana", "family": "De Leo"},
        {"given": "Enrico", "family": "Zammarchi"},
        {"given": "Pier Giorgio", "family": "Natali"},
        {"given": "Donato", "family": "Civitareale"},
    ]


class ReferenceWithDocumentFactory(ReferenceFactory):
    document = factory.SubFactory(
        BibliographyEntryFactory,
        id=factory.SelfAttribute("..id")
    )
