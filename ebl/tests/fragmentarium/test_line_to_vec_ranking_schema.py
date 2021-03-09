from ebl.fragmentarium.application.fragment_matcher import LineToVecRanking
from ebl.fragmentarium.application.line_to_vec import LineToVecScore
from ebl.fragmentarium.application.line_to_vec_ranking_schema import (
    LineToVecRankingSchema,
)
from ebl.fragmentarium.domain.museum_number import MuseumNumber


def test_line_to_vec_ranking_schema():
    line_to_vec_ranking = LineToVecRanking(
        score=[
            LineToVecScore(MuseumNumber.of("X.0"), "N/A", 10),
            LineToVecScore(MuseumNumber.of("X.1"), "N/A", 4),
        ],
        score_weighted=[
            LineToVecScore(MuseumNumber.of("X.0"), "N/A", 15),
            LineToVecScore(MuseumNumber.of("X.1"), "N/A", 7),
        ],
    )
    assert LineToVecRankingSchema().dump(line_to_vec_ranking) == {
        "score": [
            {"id": "X.0", "score": 10, "script": "N/A"},
            {"id": "X.1", "score": 4, "script": "N/A"},
        ],
        "scoreWeighted": [
            {"id": "X.0", "score": 15, "script": "N/A"},
            {"id": "X.1", "score": 7, "script": "N/A"},
        ],
    }
