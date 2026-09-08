from ebl.bibliography.domain.reference import BibliographyId, Reference, ReferenceType
from ebl.common.domain.period import Period
from ebl.fragmentarium.domain.fragment import Script
from ebl.fragmentarium.domain.fragment_query_summary import FragmentQuerySummary
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.transliteration.domain.museum_number import MuseumNumber


def reference_of(id_: str, type_: ReferenceType = ReferenceType.COPY) -> Reference:
    return ReferenceFactory.build(id=BibliographyId(id_), type=type_)


def summary_of(number: str, *references: Reference) -> FragmentQuerySummary:
    return FragmentQuerySummary(
        museum_number=MuseumNumber.of(number),
        description="",
        script=Script(Period.NEO_ASSYRIAN),
        references=references,
    )
