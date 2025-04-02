import attr

from ebl.fragmentarium.domain.fragment_info import FragmentInfo
from ebl.fragmentarium.domain.record import Record, RecordEntry, RecordType
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.fragment import FragmentFactory
from ebl.transliteration.domain.lark_parser import parse_atf_lark

FRAGMENT = FragmentFactory.build()
FRAGMENT_WITH_REFERENCES = FragmentFactory.build(
    references=(ReferenceFactory.build(), ReferenceFactory.build())
)
MATCHING_LINES = parse_atf_lark("1. kur")


def test_of():
    assert FragmentInfo.of(FRAGMENT, MATCHING_LINES) == FragmentInfo(
        FRAGMENT.number,
        FRAGMENT.accession,
        FRAGMENT.script,
        FRAGMENT.acquisition,
        FRAGMENT.description,
        MATCHING_LINES,
        "",
        "",
        genres=FRAGMENT.genres,
    )


def test_of_with_references():
    assert FragmentInfo.of(FRAGMENT_WITH_REFERENCES, MATCHING_LINES) == FragmentInfo(
        FRAGMENT_WITH_REFERENCES.number,
        FRAGMENT_WITH_REFERENCES.accession,
        FRAGMENT_WITH_REFERENCES.script,
        FRAGMENT_WITH_REFERENCES.acquisition,
        FRAGMENT_WITH_REFERENCES.description,
        MATCHING_LINES,
        "",
        "",
        FRAGMENT_WITH_REFERENCES.references,
        genres=FRAGMENT_WITH_REFERENCES.genres,
    )


def test_of_with_record():
    fragment = attr.evolve(
        FRAGMENT,
        record=Record(
            (
                RecordEntry(
                    "Not This User", RecordType.REVISION, "2017-06-20T00:00:00.000Z"
                ),
                RecordEntry(
                    "Not This User",
                    RecordType.HISTORICAL_TRANSLITERATION,
                    "2015-06-20/2017-06-20",
                ),
                RecordEntry(
                    "Not This User", RecordType.COLLATION, "2017-06-20T00:00:00.000Z"
                ),
                RecordEntry(
                    "This User", RecordType.TRANSLITERATION, "2018-06-20T00:00:00.000Z"
                ),
            )
        ),
    )
    assert FragmentInfo.of(fragment, MATCHING_LINES) == FragmentInfo(
        FRAGMENT.number,
        FRAGMENT.accession,
        FRAGMENT.script,
        FRAGMENT.acquisition,
        FRAGMENT.description,
        MATCHING_LINES,
        "This User",
        "2018-06-20T00:00:00.000Z",
        genres=FRAGMENT.genres,
    )


def test_of_defaults():
    assert FragmentInfo.of(FRAGMENT).matching_lines is None
