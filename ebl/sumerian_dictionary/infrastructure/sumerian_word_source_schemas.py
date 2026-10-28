from marshmallow import fields

from ebl.sumerian_dictionary.domain.sumerian_word import (
    AttingerHeadword,
    AttingerSource,
    Epsd2Source,
    Match,
    Sources,
)
from ebl.sumerian_dictionary.infrastructure.sumerian_schema_base import AttrsSchema


class AttingerHeadwordSchema(AttrsSchema):
    model = AttingerHeadword

    text = fields.String(required=True)
    display = fields.String(required=True)
    marks = fields.List(
        fields.Tuple((fields.Integer(), fields.Integer(), fields.String())),
        load_default=list,
    )


class AttingerSourceSchema(AttrsSchema):
    model = AttingerSource

    entry_id = fields.String(required=True, data_key="entryId")
    node = fields.String(required=True)
    letter = fields.String(required=True)
    depth = fields.Integer(required=True)
    part_of_speech = fields.String(required=True, data_key="partOfSpeech")
    headword = fields.Nested(AttingerHeadwordSchema, required=True)


class Epsd2SourceSchema(AttrsSchema):
    model = Epsd2Source

    oid = fields.String(required=True)
    headword = fields.String(required=True)
    builds = fields.List(fields.String(), load_default=list)


class SourcesSchema(AttrsSchema):
    model = Sources

    attinger = fields.Nested(AttingerSourceSchema, allow_none=True, load_default=None)
    epsd2 = fields.Nested(Epsd2SourceSchema, allow_none=True, load_default=None)


class MatchSchema(AttrsSchema):
    model = Match

    tier = fields.String(required=True)
    method = fields.String(required=True)
    spelling = fields.String(required=True)
    candidate_count = fields.Integer(required=True, data_key="candidateCount")
    curated = fields.Boolean(required=True)
    curated_oid = fields.String(data_key="curatedOid", load_default="")
    curated_status = fields.String(data_key="curatedStatus", load_default="")
    oid_status = fields.String(data_key="oidStatus", load_default="")
    review = fields.List(fields.String(), load_default=list)
