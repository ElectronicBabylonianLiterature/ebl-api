from ebl.fragmentarium.application.fragment_matcher import LineToVecRanking
from ebl.fragmentarium.application.fragment_schema import ScriptSchema
from ebl.fragmentarium.application.line_to_vec import LineToVecScore
from ebl.fragmentarium.application.line_to_vec_ranking_schema import (
    LineToVecRankingSchema,
)
from ebl.fragmentarium.domain.fragment import Script
from ebl.transliteration.domain.museum_number import MuseumNumber

SCRIPT = Script()
SERIALIZED_SCRIPT = ScriptSchema().dump(SCRIPT)


def test_line_to_vec_ranking_schema():
    line_to_vec_ranking = LineToVecRanking(
        score=[
            LineToVecScore(MuseumNumber.of("X.0"), SCRIPT, 10),
            LineToVecScore(MuseumNumber.of("X.1"), SCRIPT, 4),
        ],
        score_weighted=[
            LineToVecScore(MuseumNumber.of("X.0"), SCRIPT, 15),
            LineToVecScore(MuseumNumber.of("X.1"), SCRIPT, 7),
        ],
    )
    assert LineToVecRankingSchema().dump(line_to_vec_ranking) == {
        "score": [
            {"museumNumber": "X.0", "score": 10, "script": SERIALIZED_SCRIPT},
            {"museumNumber": "X.1", "score": 4, "script": SERIALIZED_SCRIPT},
        ],
        "scoreWeighted": [
            {"museumNumber": "X.0", "score": 15, "script": SERIALIZED_SCRIPT},
            {"museumNumber": "X.1", "score": 7, "script": SERIALIZED_SCRIPT},
        ],
    }
