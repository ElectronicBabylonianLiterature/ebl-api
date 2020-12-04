from marshmallow import Schema, post_load, fields  # pyre-ignore[21]

from ebl.fragmentarium.application.fragment_matcher import LineToVecRanking


class LineToVecRankingSchema(Schema):  # pyre-ignore[11]
    score = fields.List(fields.Tuple((fields.String(), fields.Int())), required=True)
    score_weighted = fields.List(
        fields.Tuple((fields.String(), fields.Int())),
        data_key="scoreWeighted",
        required=True,
    )

    @post_load  # pyre-ignore[56]
    def make_line_to_vec_ranking(self, data, **kwargs) -> LineToVecRanking:
        return LineToVecRanking(**data)
