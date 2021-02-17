from marshmallow import Schema, fields, pre_dump


class LineToVecRankingSchema(Schema):
    score = fields.List(fields.Tuple((fields.String(), fields.Int())), required=True)
    score_weighted = fields.List(
        fields.Tuple((fields.String(), fields.Int())),
        required=True,
        data_key="scoreWeighted",
    )

    @pre_dump
    def make_museum_number_to_str(self, data, **kwargs):
        return {
            "score": [
                (str(museum_number), score) for museum_number, score in data.score
            ],
            "score_weighted": [
                (str(museum_number), score)
                for museum_number, score in data.score_weighted
            ],
        }
