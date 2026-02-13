import pydash
from marshmallow import Schema, fields, post_load, post_dump

from ebl.common.domain.provenance_model import GeoCoordinate, ProvenanceRecord


class GeoCoordinateSchema(Schema):
    latitude = fields.Float(required=True)
    longitude = fields.Float(required=True)
    uncertainty_radius_km = fields.Float(
        allow_none=True, data_key="uncertaintyRadiusKm"
    )
    notes = fields.String(allow_none=True)

    @post_load
    def make_geo_coordinate(self, data, **kwargs) -> GeoCoordinate:
        return GeoCoordinate(**data)

    @post_dump
    def filter_none(self, data, **kwargs):
        return pydash.omit_by(data, pydash.is_none)


class ProvenanceRecordSchema(Schema):
    id = fields.String(data_key="_id")
    long_name = fields.String(required=True, data_key="longName")
    abbreviation = fields.String(required=True)
    parent = fields.String(allow_none=True)
    cigs_key = fields.String(allow_none=True, data_key="cigsKey")
    sort_key = fields.Integer(load_default=-1, data_key="sortKey")
    coordinates = fields.Nested(GeoCoordinateSchema, allow_none=True)

    @post_load
    def make_provenance_record(self, data, **kwargs) -> ProvenanceRecord:
        return ProvenanceRecord(**data)

    @post_dump
    def filter_none(self, data, **kwargs):
        return pydash.omit_by(data, pydash.is_none)


class ApiProvenanceRecordSchema(ProvenanceRecordSchema):
    id = fields.String(required=True, dump_only=True)
