import attr

from ebl.fragmentarium.domain.fragment_info import FragmentInfo
from ebl.fragmentarium.domain.record import Record, RecordEntry, RecordType
from ebl.tests.factories.fragment import FragmentFactory

FRAGMENT = FragmentFactory.build()


def test_of():
    matching_lines = (('1. kur', ), )
    assert FragmentInfo.of(FRAGMENT, matching_lines) == FragmentInfo(
        FRAGMENT.number,
        FRAGMENT.accession,
        FRAGMENT.script,
        FRAGMENT.description,
        matching_lines,
        '',
        ''
    )


def test_of_with_record():
    fragment = attr.evolve(FRAGMENT, record=Record((
        RecordEntry('Not This User', RecordType.REVISION,
                    '2017-06-20T00:00:00.000Z'),
        RecordEntry('Not This User', RecordType.HISTORICAL_TRANSLITERATION,
                    '2015-06-20/2017-06-20'),
        RecordEntry('Not This User', RecordType.COLLATION,
                    '2017-06-20T00:00:00.000Z'),
        RecordEntry('This User', RecordType.TRANSLITERATION,
                    '2018-06-20T00:00:00.000Z')
    )))
    matching_lines = (('1. kur', ), )
    assert FragmentInfo.of(fragment, matching_lines) == FragmentInfo(
        FRAGMENT.number,
        FRAGMENT.accession,
        FRAGMENT.script,
        FRAGMENT.description,
        matching_lines,
        'This User',
        '2018-06-20T00:00:00.000Z'
    )


def test_of_defaults():
    assert FragmentInfo.of(FRAGMENT).matching_lines == tuple()
