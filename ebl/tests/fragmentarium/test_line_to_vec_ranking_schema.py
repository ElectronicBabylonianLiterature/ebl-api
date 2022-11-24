from ebl.fragmentarium.application.fragment_matcher import LineToVecRanking
from ebl.fragmentarium.application.line_to_vec import LineToVecScore
from ebl.fragmentarium.application.line_to_vec_ranking_schema import (
    LineToVecRankingSchema,
)
from ebl.transliteration.domain.museum_number import MuseumNumber


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
            {"museumNumber": "X.0", "score": 10, "legacyScript": "N/A"},
            {"museumNumber": "X.1", "score": 4, "legacyScript": "N/A"},
        ],
        "scoreWeighted": [
            {"museumNumber": "X.0", "score": 15, "legacyScript": "N/A"},
            {"museumNumber": "X.1", "score": 7, "legacyScript": "N/A"},
        ],
    }
