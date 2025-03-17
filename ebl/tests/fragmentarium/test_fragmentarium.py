from ebl.fragmentarium.domain.fragment_info import FragmentInfo
from ebl.tests.factories.fragment import TransliteratedFragmentFactory


def test_needs_revision(fragmentarium, fragment_repository, when):
    fragment_info = FragmentInfo.of(TransliteratedFragmentFactory.build())
    (
        when(fragment_repository)
        .query_by_transliterated_not_revised_by_other(())
        .thenReturn([fragment_info])
    )
    assert fragmentarium.find_needs_revision() == [fragment_info]


def test_statistics(fragmentarium, fragment_repository, when):
    transliterated_fragments = 2
    lines = 4
    total_fragments = 0

    (
        when(fragment_repository)
        .count_transliterated_fragments()
        .thenReturn(transliterated_fragments)
    )
    when(fragment_repository).count_lines().thenReturn(lines)
    when(fragment_repository).count_total_fragments().thenReturn(total_fragments)

    assert fragmentarium.statistics() == {
        "transliteratedFragments": transliterated_fragments,
        "lines": lines,
        "totalFragments": total_fragments
    }
