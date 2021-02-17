import pytest

from ebl.fragmentarium.application.fragment_matcher import LineToVecRanking
from ebl.fragmentarium.application.fragment_matcher import sort_scores_to_list
from ebl.fragmentarium.domain.line_to_vec_encoding import LineToVecEncoding
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.tests.factories.fragment import FragmentFactory


def test_find(fragment_matcher, fragment_repository, when):
    line_to_vec = (LineToVecEncoding.from_list((1, 2, 1, 1)),)
    number = MuseumNumber.of("BM.11")
    fragment = FragmentFactory.build(number=number, line_to_vec=line_to_vec)
    (when(fragment_repository).query_by_museum_number(number).thenReturn(fragment))
    assert fragment_matcher._parse_candidate("BM.11") == line_to_vec


def test_sort_scores_to_list(fragment_matcher):
    score = {"FragmentId1": 4, "FragmentId2": 12, "FragmentId3": 2}
    assert sort_scores_to_list(score) == [
        ("FragmentId2", 12),
        ("FragmentId1", 4),
        ("FragmentId3", 2),
    ]


@pytest.mark.parametrize(
    "parameters, expected",
    [
        [
            "BM.11",
            {
                "score": [(MuseumNumber.of("X.1"), 0)],
                "score_weighted": [(MuseumNumber.of("X.1"), 0)],
            },
        ]
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
    [fragment_repository.create(fragment) for fragment in [fragment_1, fragment_2]]
    (
        when(fragment_repository)
        .query_transliterated_line_to_vec()
        .thenReturn(
            {
                fragment_1.number: (fragment_1_line_to_vec,),
                fragment_2.number: (fragment_2_line_to_vec,),
            }
        )
    )
    assert fragment_matcher.rank_line_to_vec(parameters) == LineToVecRanking(**expected)
