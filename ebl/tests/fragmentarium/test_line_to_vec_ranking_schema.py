from ebl.fragmentarium.application.fragment_matcher import LineToVecRanking
from ebl.fragmentarium.application.line_to_vec import LineToVecScore
from ebl.fragmentarium.application.line_to_vec_ranking_schema import (
    LineToVecRankingSchema,
)

from ebl.transliteration.domain.museum_number import MuseumNumber


def test_line_to_vec_ranking_schema():
    line_to_vec_ranking = LineToVecRanking(
        score=[
            LineToVecScore(MuseumNumber.of("X.0"), "NA", 10),
            LineToVecScore(MuseumNumber.of("X.1"), "NA", 4),
        ],
        score_weighted=[
            LineToVecScore(MuseumNumber.of("X.0"), "NA", 15),
            LineToVecScore(MuseumNumber.of("X.1"), "NA", 7),
        ],
    )
    assert LineToVecRankingSchema().dump(line_to_vec_ranking) == {
        "score": [
            {"museumNumber": "X.0", "score": 10, "script": "NA"},
            {"museumNumber": "X.1", "score": 4, "script": "NA"},
        ],
        "scoreWeighted": [
            {"museumNumber": "X.0", "score": 15, "script": "NA"},
            {"museumNumber": "X.1", "score": 7, "script": "NA"},
        ],
    }
