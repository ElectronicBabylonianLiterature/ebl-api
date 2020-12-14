from ebl.fragmentarium.application.fragment_matcher import LineToVecRanking
from ebl.fragmentarium.application.line_to_vec_ranking_schema import (
    LineToVecRankingSchema,
)
from ebl.fragmentarium.domain.museum_number import MuseumNumber


def test_line_to_vec_ranking_schema():
    line_to_vec_ranking = LineToVecRanking(
        score=[(MuseumNumber.of("X.0"), 10), (MuseumNumber.of("X.0"), 5)],
        score_weighted=[(MuseumNumber.of("X.0"), 15), (MuseumNumber.of("X.0"), 3)],
    )
    assert LineToVecRankingSchema().dump(line_to_vec_ranking) == {
        "score": [("X.0", 10), ("X.0", 5)],
        "scoreWeighted": [("X.0", 15), ("X.0", 3)],
    }
