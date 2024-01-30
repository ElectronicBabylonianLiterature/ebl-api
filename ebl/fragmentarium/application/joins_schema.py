from marshmallow import Schema, fields, post_load

from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.fragmentarium.domain.joins import Join, Joins


class JoinSchema(Schema):
    museum_number = fields.Nested(
        MuseumNumberSchema, required=True, data_key="museumNumber"
    )
    is_checked = fields.Boolean(required=True, data_key="isChecked")
    joined_by = fields.String(required=True, data_key="joinedBy")
    date = fields.String(required=True)
    note = fields.String(required=True)
    legacy_data = fields.String(required=True, data_key="legacyData")
    is_in_fragmentarium = fields.Boolean(
        load_default=False, data_key="isInFragmentarium")
    is_envelope = fields.Boolean(
        load_default=False, data_key="isEnvelope" )


    @post_load
    def make_join(self, data, **kwargs):
        return Join(**data)


class JoinsSchema(Schema):
    fragments = fields.List(fields.List(fields.Nested(JoinSchema)))

    @post_load
    def make_joins(self, data, **kwargs):
        return Joins(tuple(map(tuple, data["fragments"])))
