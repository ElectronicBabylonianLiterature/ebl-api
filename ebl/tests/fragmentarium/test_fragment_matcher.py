import pytest  # pyre-ignore[21]

from ebl.fragmentarium.application.matches.create_line_to_vec import LineToVecEncoding
from ebl.fragmentarium.application.fragment_matcher import LineToVecRanking
from ebl.fragmentarium.application.line_to_vec_ranking_schema import (
    LineToVecRankingSchema,
)
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.fragmentarium.application.fragment_matcher import sort_scores_to_list
from ebl.tests.factories.fragment import FragmentFactory


def test_parse_candidate(fragment_matcher, fragment_repository, when):
    line_to_vec = (LineToVecEncoding.from_list((1, 2, 1, 1)),)
    number = MuseumNumber.of("BM.11")
    fragment = FragmentFactory.build(number=number, line_to_vec=line_to_vec)
    (when(fragment_repository).query_by_museum_number(number).thenReturn(fragment))
    assert fragment_matcher.parse_candidate("BM.11") == line_to_vec
    assert fragment_matcher.parse_candidate(((1, 2, 1, 1),)) == line_to_vec


def test_sort_scores_to_list(fragment_matcher):
    score = {"FragmentId1": 4, "FragmentId2": 12, "FragmentId3": 2}
    assert sort_scores_to_list(score) == [
        ("FragmentId2", 12),
        ("FragmentId1", 4),
        ("FragmentId3", 2),
    ]


def test_line_to_vec_ranking_schema():
    line_to_vec_ranking = LineToVecRanking(
        [("X.0", 2), ("X.1", 1)], [("X.0", 6), ("X.1", 2)]
    )
    schema = LineToVecRankingSchema()
    data = schema.dump(line_to_vec_ranking)
    assert schema.load(data) == line_to_vec_ranking


@pytest.mark.parametrize(
    "parameters, expected",
    [
        ["BM.11", {"score": [("X.1", 0)], "score_weighted": [("X.1", 0)]}],
        [
            ((1, 2, 1, 1),),
            {
                "score": [("BM.11", 0), ("X.1", 0)],
                "score_weighted": [("BM.11", 0), ("X.1", 0)],
            },
        ],
    ],
)
def test_line_to_vec(parameters, expected, fragment_matcher, when, fragment_repository):
    fragment_1_line_to_vec = (LineToVecEncoding.from_list([1, 2, 1, 1]),)
    fragment_2_line_to_vec = (LineToVecEncoding.from_list([2, 1, 1]),)
    fragment_1 = FragmentFactory.build(
        number=MuseumNumber.of("BM.11"), line_to_vec=fragment_1_line_to_vec
    )
    fragment_2 = FragmentFactory.build(
        number=MuseumNumber.of("X.1"), line_to_vec=fragment_2_line_to_vec
    )
    fragment_3 = FragmentFactory.build(line_to_vec=None)
    [
        fragment_repository.create(fragment)
        for fragment in [fragment_1, fragment_2, fragment_3]
    ]
    (
        when(fragment_repository)
        .query_transliterated_line_to_vec()
        .thenReturn(
            {
                str(fragment_1.number): (fragment_1_line_to_vec,),
                str(fragment_2.number): (fragment_2_line_to_vec,),
            }
        )
    )
    assert fragment_matcher.rank_line_to_vec(parameters) == LineToVecRanking(**expected)
