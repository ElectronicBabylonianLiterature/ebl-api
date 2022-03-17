from marshmallow import Schema, fields, post_load, EXCLUDE

from ebl.fragmentarium.domain.annotation import (
    Geometry,
    AnnotationData,
    Annotation,
    Annotations,
    AnnotationValueType,
)
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.schemas import ValueEnum


class GeometrySchema(Schema):
    x = fields.Float(required=True)
    y = fields.Float(required=True)
    width = fields.Float(required=True)
    height = fields.Float(required=True)

    @post_load
    def make_geometry(self, data, **kwargs):
        return Geometry(**data)


class AnnotationDataSchema(Schema):
    id = fields.String(required=True)
    type = ValueEnum(AnnotationValueType, load_default=AnnotationValueType.HAS_SIGN)
    sign_name = fields.String(load_default="", data_key="signName")
    value = fields.String(required=True)
    path = fields.List(fields.Int, required=True)

    @post_load
    def make_data(self, data, **kwargs):
        return AnnotationData(**data)


class AnnotationSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    geometry = fields.Nested(GeometrySchema(), required=True)
    data = fields.Nested(AnnotationDataSchema(), required=True)

    @post_load
    def make_annotation(self, data, **kwargs):
        return Annotation(**data)


class AnnotationsSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    fragment_number = fields.String(required=True, data_key="fragmentNumber")
    annotations = fields.Nested(AnnotationSchema, many=True, required=True)

    @post_load
    def make_annotation(self, data, **kwargs):
        data["fragment_number"] = MuseumNumber.of(data["fragment_number"])
        return Annotations(**data)
