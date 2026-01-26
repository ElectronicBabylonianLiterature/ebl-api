from ebl.common.domain.period import Period
from ebl.fragmentarium.application.fragment_matcher import (
    sort_scores_to_list,
    LineToVecRanking,
)
from ebl.fragmentarium.application.line_to_vec import LineToVecScore, LineToVecEntry
from ebl.fragmentarium.domain.line_to_vec_encoding import LineToVecEncoding
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.tests.factories.fragment import FragmentFactory, ScriptFactory


def test_find(fragment_repository, when, fragment_matcher):
    line_to_vec = (LineToVecEncoding.from_list((1, 2, 1, 1)),)
    number = MuseumNumber.of("BM.11")
    fragment = FragmentFactory.build(number=number, line_to_vec=line_to_vec)
    (when(fragment_repository).query_by_museum_number(number).thenReturn(fragment))
    assert fragment_matcher._parse_candidate("BM.11") == line_to_vec


SCRIPT = ScriptFactory.build(period=Period.NEO_ASSYRIAN)


def test_sort_scores_to_list():
    score = [
        LineToVecScore(MuseumNumber.of("X.1"), SCRIPT, 4),
        LineToVecScore(MuseumNumber.of("X.2"), SCRIPT, 12),
        LineToVecScore(MuseumNumber.of("X.3"), SCRIPT, 2),
    ]

    assert sort_scores_to_list(score) == [
        LineToVecScore(MuseumNumber.of("X.2"), SCRIPT, 12),
        LineToVecScore(MuseumNumber.of("X.1"), SCRIPT, 4),
        LineToVecScore(MuseumNumber.of("X.3"), SCRIPT, 2),
    ]


def test_line_to_vec(fragment_matcher, when):
    parameters = "BM.11"
    fragment_1_line_to_vec = (LineToVecEncoding.from_list([1, 2, 1, 1]),)
    fragment_2_line_to_vec = (LineToVecEncoding.from_list([2, 1, 1]),)
    fragment_1 = FragmentFactory.build(
        number=MuseumNumber.of("BM.11"), line_to_vec=fragment_1_line_to_vec
    )
    fragment_2 = FragmentFactory.build(
        number=MuseumNumber.of("X.1"), line_to_vec=fragment_2_line_to_vec
    )

    (
        when(fragment_matcher._fragment_repository)
        .query_by_museum_number(MuseumNumber.of(parameters))
        .thenReturn(fragment_1)
    )
    (
        when(fragment_matcher._fragment_repository)
        .query_transliterated_line_to_vec()
        .thenReturn(
            [
                LineToVecEntry(fragment_1.number, SCRIPT, fragment_1_line_to_vec),
                LineToVecEntry(fragment_2.number, SCRIPT, fragment_2_line_to_vec),
            ]
        )
    )
    assert fragment_matcher.rank_line_to_vec(parameters) == LineToVecRanking(
        [LineToVecScore(MuseumNumber.of("X.1"), SCRIPT, 3)],
        [LineToVecScore(MuseumNumber.of("X.1"), SCRIPT, 5)],
    )


def test_empty_line_to_vec(fragment_matcher, when):
    parameters = "BM.11"
    fragment_2_line_to_vec = (LineToVecEncoding.from_list([2, 1, 1]),)
    fragment_1 = FragmentFactory.build(number=MuseumNumber.of("BM.11"))
    fragment_2 = FragmentFactory.build(
        number=MuseumNumber.of("X.1"), line_to_vec=fragment_2_line_to_vec
    )
    fragment_3 = FragmentFactory.build(
        number=MuseumNumber.of("X.2"), line_to_vec=fragment_2_line_to_vec
    )

    (
        when(fragment_matcher._fragment_repository)
        .query_by_museum_number(MuseumNumber.of(parameters))
        .thenReturn(fragment_1)
    )
    (
        when(fragment_matcher._fragment_repository)
        .query_transliterated_line_to_vec()
        .thenReturn(
            [
                LineToVecEntry(fragment_1.number, SCRIPT, ()),
                LineToVecEntry(fragment_2.number, SCRIPT, fragment_2_line_to_vec),
                LineToVecEntry(fragment_3.number, SCRIPT, fragment_2_line_to_vec),
            ]
        )
    )
    assert fragment_matcher.rank_line_to_vec(parameters) == LineToVecRanking([], [])
