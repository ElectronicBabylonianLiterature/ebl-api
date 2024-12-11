from marshmallow import Schema, fields, pre_dump
from ebl.fragmentarium.application.line_to_vec import LineToVecScore
from ebl.fragmentarium.application.fragment_fields_schemas import ScriptSchema
from ebl.fragmentarium.domain.fragment import Script


class LineToVecScoreSchema(Schema):
    museum_number = fields.String(required=True, data_key="museumNumber")
    script = fields.Nested(ScriptSchema, load_default=Script())
    score = fields.Int(required=True)

    @pre_dump
    def make_museum_number_to_str(self, line_to_vec_score: LineToVecScore, **kwargs):
        return {
            "museum_number": str(line_to_vec_score.museum_number),
            "script": line_to_vec_score.script,
            "score": line_to_vec_score.score,
        }


class LineToVecRankingSchema(Schema):
    score = fields.Nested(LineToVecScoreSchema, many=True)
    score_weighted = fields.Nested(
        LineToVecScoreSchema, many=True, required=True, data_key="scoreWeighted"
    )
