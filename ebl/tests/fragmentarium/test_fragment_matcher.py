import pytest  # pyre-ignore[21]

from ebl.fragmentarium.domain.fragment import LineToVecEncoding
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.tests.factories.fragment import FragmentFactory


def test_find(fragment_matcher, fragment_repository, when):
    line_to_vec = LineToVecEncoding.from_list((1, 2, 1, 1))
    number = MuseumNumber.of("BM.11")
    fragment = FragmentFactory.build(number=number, line_to_vec=line_to_vec)
    (when(fragment_repository).query_by_museum_number(number).thenReturn(fragment))
    assert fragment_matcher.parse_candidate("BM.11") == line_to_vec
    assert fragment_matcher.parse_candidate((1, 2, 1, 1)) == line_to_vec


def test_sort_dict_desc(fragment_matcher):
    score = {"FragmentId1": 4, "FragmentId2": 12, "FragmentId3": 2}
    assert fragment_matcher._sort_dict_desc(score) == {
        "FragmentId2": 12,
        "FragmentId1": 4,
        "FragmentId3": 2,
    }


@pytest.mark.parametrize("parameters", ["BM.11", [1, 2, 1, 1]])
def test_line_to_vec(parameters, fragment_matcher, when, fragment_repository):
    fragment_1_line_to_vec = LineToVecEncoding.from_list([1, 2, 1, 1])
    fragment_2_line_to_vec = LineToVecEncoding.from_list([2, 1, 1])
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
                str(fragment_1.number): fragment_1_line_to_vec,
                str(fragment_2.number): fragment_2_line_to_vec,
            }
        )
    )
    assert fragment_matcher.line_to_vec(parameters) == {
        "score": [("BM.11", 4), ("X.1", 3)],
        "score_weighted": [("BM.11", 3), ("X.1", 3)],
    }
